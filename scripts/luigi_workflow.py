#!/usr/bin/env python

import time
import luigi
from luigi import Parameter, LocalTarget
from luigi.util import inherits, requires
from glob import glob
from os.path import join as pjoin, abspath, isdir

from plumbum import local
from shutil import rmtree

from align import work_flow as align_wf
from pnl_eddy import work_flow as pnl_eddy_wf
from bet_mask import work_flow as bet_mask_wf
from bse import work_flow as bse_wf
from ukf import work_flow as ukf_wf

from _define_outputs import define_outputs_wf, create_dirs

class SelectFiles(luigi.Task):

    id= Parameter()
    bids_data_dir= Parameter()
    dwi_template= Parameter()

    def output(self):
        id_template= self.dwi_template.replace('id',self.id)

        dwi= local.path(glob(pjoin(abspath(bids_data_dir), id_template))[0])
        bval= dwi.with_suffix('.bval', depth=2)
        bvec= dwi.with_suffix('.bvec', depth=2)

        return dict(dwi= dwi, bval= bval, bvec= bvec)

        

@requires(SelectFiles)
class DwiAlign(luigi.Task):

    dwi_align_prefix=Parameter()

    def run(self):
        align_wf(img_file= self.input()['dwi'],
                 bval_file= self.input()['bval'],
                 bvec_file=self.input()['bvec'],
                 out_prefix=dwi_align_prefix)

    def output(self):
        dwi= self.dwi_align_prefix.with_suffix('.nii.gz')
        bval= self.dwi_align_prefix.with_suffix('.bval')
        bvec= self.dwi_align_prefix.with_suffix('.bvec')
        
        return dict(aligned_dwi= dwi, aligned_bval= bval, aligned_bvec= bvec)



@requires(DwiAlign)
class PnlEddy(luigi.Task):

    eddy_prefix= Parameter()

    def run(self):
        pnl_eddy_wf(dwi= self.input()['aligned_dwi'],
                    bvalFile= self.input()['aligned_bval'],
                    bvecFile= self.input()['aligned_bvec'],
                    out= self.eddy_prefix)
                    
    def output(self):
        dwi= self.eddy_prefix.with_suffix('.nii.gz')
        bval= self.eddy_prefix.with_suffix('.bval')
        bvec= self.eddy_prefix.with_suffix('.bvec')

        return dict(eddy_dwi= dwi, eddy_bval= bval, eddy_bvec= bvec)



@requires(PnlEddy)
class BseExtract(luigi.Task):
    
    bse_prefix= Parameter()
    
    def run(self):
        bse_wf(dwi=self.input()['eddy_dwi'],
               bval_file= self.input()['eddy_bval'],
               out= self.output())
               
    def output(self):
        return self.bse_prefix.with_suffix('.nii.gz')

   
        
@requires(BseExtract)
class BetMask(luigi.Task):
    
    bse_betmask_prefix= Parameter()
    
    def run(self):
        bet_mask_wf(img=self.input(),
                    out=self.bse_betmask_prefix)
               
    def output(self):
        return local.path(self.bse_betmask_prefix._path+'_mask.nii.gz')
        

@inherits(PnlEddy, BetMask)
class UkfTract(luigi.Task):

    tract_prefix= Parameter()
    ukf_params= Parameter()
    
    def requires(self):
        return dict(eddy= self.clone(PnlEddy), bet_mask= self.clone(BetMask))
        
    def run(self):
        ukf_wf(dwi= self.input()['eddy']['eddy_dwi'],
               dwimask= self.input()['bet_mask'],
               bvalFile= self.input()['eddy']['eddy_bval'],
               bvecFile= self.input()['eddy']['eddy_bvec'],
               out= self.output(),
               givenParams= self.ukf_params)

    def output(self):
        return self.tract_prefix.with_suffix('.vtk')
        

def create_dirs(cases, dir):
    from shutil import rmtree
    from os import makedirs
    from os.path import isdir
    from os.path import join as pjoin
    
    makedirs(dir)
    # if not isdir(dir): 
    for id in cases:
        makedirs(pjoin(dir, f'sub-{id}', 'anat'))
        makedirs(pjoin(dir, f'sub-{id}', 'dwi'))
        makedirs(pjoin(dir, f'sub-{id}', 'tracts'))
        makedirs(pjoin(dir, f'sub-{id}', 'anat', 'freesurfer'))
        makedirs(pjoin(dir, f'sub-{id}', 'fs2dwi'))
        makedirs(pjoin(dir, f'sub-{id}', 'tracts', 'wmql'))
        makedirs(pjoin(dir, f'sub-{id}', 'tracts', 'wmqlqc'))
            
            
            
if __name__=='__main__':
    id='003GNX007'
    bids_data_dir='/home/tb571/Downloads/INTRuST_BIDS/'
    dwi_template='sub-id/dwi/*_dwi.nii.gz'
    bids_derivatives= pjoin(abspath(bids_data_dir), 'derivatives', 'pnlNipype')
    ukf_params='--seedingThreshold,0.4,--seedsPerVoxel,1'
    
    overwrite=False
    if overwrite:
        confirm= input('Are you sure you want to overwrite results? [y/n]:')
        if confirm!='y':
            overwrite=False
            print('Continuing with cached outputs')
            
    if overwrite:
        rmtree(bids_derivatives)
        create_dirs([id], bids_derivatives)
    
    (t1_align_prefix, t2_align_prefix, dwi_align_prefix,
     t1_mabsmask_prefix, t2_mabsmask_prefix, eddy_bse_betmask_prefix,
     fs_dir, fs_in_eddy, fs_in_epi,
     eddy_bse_prefix, eddy_bse_masked_prefix, eddy_epi_bse_prefix, eddy_epi_bse_masked_prefix,
     eddy_prefix, eddy_epi_prefix,
     eddy_tract_prefix, eddy_epi_tract_prefix,
     eddy_fs2dwi_dir, epi_fs2dwi_dir,
     eddy_wmql_dir, eddy_wmqlqc_dir, epi_wmql_dir, epi_wmqlqc_dir)= define_outputs_wf(id, bids_derivatives)
    
    '''
    luigi.build([SelectFiles(id, bids_data_dir, dwi_template)], local_scheduler=True)
    
    
    luigi.build([DwiAlign(id= id,
                          bids_data_dir= bids_data_dir,
                          dwi_template= dwi_template,
                          dwi_align_prefix= dwi_align_prefix)],
                local_scheduler=True)
    
    
    luigi.build([PnlEddy(id= id,
                         bids_data_dir= bids_data_dir,
                         dwi_template= dwi_template,
                         dwi_align_prefix= dwi_align_prefix,
                         eddy_prefix=eddy_prefix)],
                local_scheduler=True)
    
    
    luigi.build([BseExtract(id= id,
                     bids_data_dir= bids_data_dir,
                     dwi_template= dwi_template,
                     dwi_align_prefix= dwi_align_prefix,
                     eddy_prefix=eddy_prefix,
                     bse_prefix=eddy_bse_prefix)],
                local_scheduler=True)
    
    
    luigi.build([BetMask(id= id,
                 bids_data_dir= bids_data_dir,
                 dwi_template= dwi_template,
                 dwi_align_prefix= dwi_align_prefix,
                 eddy_prefix=eddy_prefix,
                 bse_prefix=eddy_bse_prefix,
                 bse_betmask_prefix= eddy_bse_betmask_prefix)],
            local_scheduler=True)
    '''

    luigi.build([UkfTract(id= id,
                 bids_data_dir= bids_data_dir,
                 dwi_template= dwi_template,
                 dwi_align_prefix= dwi_align_prefix,
                 eddy_prefix=eddy_prefix,
                 bse_prefix=eddy_bse_prefix,
                 bse_betmask_prefix= eddy_bse_betmask_prefix,
                 tract_prefix= eddy_tract_prefix,
                 ukf_params= ukf_params)],
            local_scheduler=True)
    
