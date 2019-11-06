#!/usr/bin/env python

from __future__ import print_function
from util import logfmt, TemporaryDirectory, N_CPU, __version__
from plumbum import local, cli, FG
from plumbum.cmd import ImageMath, bash
import sys
import os


import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


def work_flow(t1in, t1mask, t2, t2mask, out, force, ncpu):

    if not force and os.path.exists(out):
        logging.error(
            'Output directory exists, use -f/--force to force an overwrite.')
        sys.exit(1)

    with TemporaryDirectory() as tmpdir, local.env(SUBJECTS_DIR=tmpdir, FSFAST_HOME='', MNI_DIR=''):

        tmpdir = local.path(tmpdir)

        if t1mask:
            logging.info('Mask the t1')
            t1 = tmpdir / 't1masked.nii.gz'
            ImageMath('3', t1, 'm', t1in, t1mask)
            skullstrip = '-noskullstrip'

        else:
            skullstrip = '-skullstrip'
            t1 = tmpdir / 't1.nii.gz'
            t1in.copy(t1)

        if t2:
            if t2mask:
                logging.info('Mask the t2')
                t2 = tmpdir / 't2masked.nii.gz'
                ImageMath('3', t2, 'm', t2, t2mask)
                skullstrip = '-noskullstrip'

            else:
                skullstrip = '-skullstrip'
                t2 = tmpdir / 't2.nii.gz'
                t2.copy(t2)

        logging.info("Run freesurfer on " + t1)
        subjid = t1.stem

        if ncpu == '-1':
            ncpu = N_CPU

        if int(ncpu) > 1:

            if t2:
                bash[
                    '-c', 'recon-all -s ' + subjid + ' -i ' + t1 + ' -T2 ' + t2 + ' -autorecon1 ' + skullstrip + ' -parallel -openmp ' + ncpu] & FG
            else:
                bash[
                    '-c', 'recon-all -s ' + subjid + ' -i ' + t1 + ' -autorecon1 ' + skullstrip + ' -parallel -openmp ' + ncpu] & FG
            (tmpdir / subjid / 'mri/T1.mgz').copy(tmpdir / subjid / 'mri/brainmask.mgz')
            bash['-c', 'recon-all -autorecon2 -subjid ' + subjid + ' -parallel -openmp ' + ncpu] & FG
            bash['-c', 'recon-all -autorecon3 -subjid ' + subjid + ' -parallel -openmp ' + ncpu] & FG

        else:  # intentionally writing a separate block omitting parallelization attributes
            if t2:
                bash['-c', 'recon-all -s ' + subjid + ' -i ' + t1 + ' -T2 ' + t2 + ' -autorecon1 ' + skullstrip] & FG
            else:
                bash['-c', 'recon-all -s ' + subjid + ' -i ' + t1 + ' -autorecon1 ' + skullstrip] & FG
            (tmpdir / subjid / 'mri/T1.mgz').copy(tmpdir / subjid / 'mri/brainmask.mgz')
            bash['-c', 'recon-all -autorecon2 -subjid ' + subjid] & FG
            bash['-c', 'recon-all -autorecon3 -subjid ' + subjid] & FG

        logging.info("Freesurfer done.")

        (tmpdir / subjid).copy(out, override=True)  # overwrites any existing directory
        logging.info("Made " + out)


class App(cli.Application):
    """Convenient script to run Freesurfer segmentation"""

    VERSION = __version__

    t1 = cli.SwitchAttr(
        ['-i', '--input'],
        cli.ExistingFile,
        help='t1 image in nifti format (nii, nii.gz)',
        mandatory=True)

    t1mask = cli.SwitchAttr(
        ['-m', '--mask'],
        cli.ExistingFile,
        help='mask the t1 before running Freesurfer; if not provided, -skullstrip is enabled with Freesurfer segmentation',
        mandatory=False)

    t2 = cli.SwitchAttr(
        ['--t2'],
        cli.ExistingFile,
        help='t2 image in nifti format (nii, nii.gz)',
        mandatory=False)

    t2mask = cli.SwitchAttr(
        ['--t2mask'],
        cli.ExistingFile,
        help='mask the t2 before running Freesurfer, if t2 is provided but not its mask, -skullstrip is enabled with Freesurfer segmentation',
        mandatory=False)


    force = cli.Flag(
        ['-f', '--force'],
        help='if --force is used, any previous output will be overwritten')

    out = cli.SwitchAttr(
        ['-o', '--outDir'],
        help='output directory',
        mandatory=True)

    ncpu = cli.SwitchAttr(['-n', '--nproc'],
        help='number of processes/threads to use (-1 for all available) for Freesurfer segmentation',
        default= 1)

    def main(self):
        fshome = local.path(os.getenv('FREESURFER_HOME'))

        if not fshome:
            logging.error('Set FREESURFER_HOME first.')
            sys.exit(1)

        work_flow(self.t1, self.t1mask, self.t2, self.t2mask, self.out, self.force, self.ncpu)


if __name__ == '__main__':
    App.run()
