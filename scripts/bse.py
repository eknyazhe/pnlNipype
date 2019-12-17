#!/usr/bin/env python

from plumbum import cli, FG
from plumbum.cmd import fslroi, ImageMath
from conversion import read_bvals
import os
from util import load_nifti, save_nifti, B0_THRESHOLD

import numpy as np


def work_flow(dwi, bval_file, out, b0_threshold=B0_THRESHOLD, dwimask=None, minimum= False, average= False, all= False):

    prefix = dwi.name.split('.')[0]
    directory = dwi.parent

    b0_threshold = float(b0_threshold)

    if out is None:
        out = os.path.join(directory, prefix + '_bse.nii.gz')

    if dwi.endswith('.nii') or dwi.endswith('.nii.gz'):

        if not bval_file:
            bval_file = os.path.join(directory, prefix + '.bval')

        bvals = read_bvals(bval_file)
        idx = np.where([bval < b0_threshold for bval in bvals])[0]

        if len(idx) > 1:

            # default is the first b0
            if not (minimum or average or all):
                fslroi[dwi, out, idx, 1] & FG

            elif minimum:
                fslroi[dwi, out, idx, np.argsort(bvals)[0]] & FG

            elif average:
                # Load the given dwi to get image data
                dwi = load_nifti(dwi._path)
                hdr = dwi.header
                mri = dwi.get_data()

                avg_bse = np.mean(mri[:, :, :, idx], axis=3)

                # Now write back the average bse
                save_nifti(out, avg_bse, dwi.affine, hdr)


            elif all:
                fslroi[dwi, out, idx, len(idx)] & FG


        else:
            raise Exception('No b0 image found. Check the bval file.')


    else:
        raise Exception("Invalid dwi format, must be a nifti image")

    if dwimask:
        ImageMath(3, out, 'm', out, dwimask)

    return out


class App(cli.Application):
    """Extracts the baseline (b0) from a nifti DWI. Assumes
    the diffusion volumes are indexed by the last axis. Chooses the first b0 as the
    baseline image by default, with option to specify one."""

    dwimask = cli.SwitchAttr(
        ['-m', '--mask'],
        cli.ExistingFile,
        help='mask of the DWI in nifti format; if mask is provided, then baseline image is masked',
        mandatory=False)

    dwi = cli.SwitchAttr(
        ['-i', '--input'],
        cli.ExistingFile,
        help='DWI in nifti format',
        mandatory=True)

    bval_file = cli.SwitchAttr(
        '--bvals',
        cli.ExistingFile,
        help='bval file, default: dwiPrefix.bval')


    out = cli.SwitchAttr(
        ['-o', '--output'],
        help= 'extracted baseline image (default: inPrefix_bse.nii.gz)',
        mandatory=False)

    b0_threshold = cli.SwitchAttr(
        ['-t', '--threshold'],
        help= 'threshold for b0',
        mandatory=False,
        default= 45.)

    minimum= cli.Flag(['--min'],
        help= 'turn on this flag to choose minimum bvalue volume as the baseline image',
        default= False,
        mandatory= False)

    average= cli.Flag(['--avg'],
        help= '''turn on this flag to choose the average of all bvalue<threshold volumes as the baseline image, 
              you might want to use this only when eddy/motion correction has been done before''',
        default= False,
        mandatory= False)

    all= cli.Flag(['--all'],
        help= '''turn on this flag to choose all bvalue<threshold volumes as the baseline image, 
              this is an useful option if you want to feed B0 into topup/eddy_openmp''',
        default= False,
        mandatory= False)


    def main(self):

        work_flow(self.dwi, self.bval_file, self.out, self.b0_threshold, self.dwimask,
                  self.minimum, self.average, self.all)


if __name__ == '__main__':
    App.run()
