from os.path import join as pjoin
from plumbum import local

# ============================================================================================================
def define_outputs_wf(id, dir):
    '''
    :param id: subject_id
    :param dir: /path/to/derivatives/ directory
    :param force: delete previous outputs
    :return: output of each script
    '''
    from os.path import join as pjoin

    t1_align_prefix = pjoin(dir, f'sub-{id}', 'anat', f'sub-{id}_desc-Xc_T1w')
    t2_align_prefix = pjoin(dir, f'sub-{id}', 'anat', f'sub-{id}_desc-Xc_T2w')
    dwi_align_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-Xc_dwi')

    t1_mabsmask_prefix = pjoin(dir, f'sub-{id}', 'anat', f'sub-{id}_desc-T1wXcMabs')
    t2_mabsmask_prefix = pjoin(dir, f'sub-{id}', 'anat', f'sub-{id}_desc-T2wXcMabs')
    
    fs_dir = pjoin(dir, f'sub-{id}', 'anat', 'freesurfer')

    eddy_bse_betmask_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-XcBseBet')

    eddy_bse_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-dwiXcEd_bse')
    eddy_bse_masked_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-dwiXcEdMa_bse')
    eddy_epi_bse_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-dwiXcEdEp_bse')
    eddy_epi_bse_masked_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-dwiXcEdEpMa_bse')

    eddy_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-XcEd_dwi')
    eddy_epi_prefix = pjoin(dir, f'sub-{id}', 'dwi', f'sub-{id}_desc-XcEdEp_dwi')
    
    eddy_fs2dwi_dir = pjoin(dir, f'sub-{id}', 'fs2dwi', 'eddy_fs2dwi')
    fs_in_eddy = pjoin(dir, f'sub-{id}', 'fs2dwi', 'eddy_fs2dwi', 'wmparcInDwi.nii.gz')
    epi_fs2dwi_dir = pjoin(dir, f'sub-{id}', 'fs2dwi', 'epi_fs2dwi')
    fs_in_epi = pjoin(dir, f'sub-{id}', 'fs2dwi', 'epi_fs2dwi', 'wmparcInDwi.nii.gz')

    eddy_tract_prefix = pjoin(dir, f'sub-{id}', 'tracts', f'sub-{id}_desc-XcEd')
    eddy_epi_tract_prefix = pjoin(dir, f'sub-{id}', 'tracts', f'sub-{id}_desc-XcEdEp')

    eddy_wmql_dir = pjoin(dir, f'sub-{id}', 'tracts', 'wmql', 'eddy')
    eddy_wmqlqc_dir = pjoin(dir, f'sub-{id}', 'tracts', 'wmqlqc', 'eddy')
    epi_wmql_dir = pjoin(dir, f'sub-{id}', 'tracts', 'wmql', 'epi')
    epi_wmqlqc_dir = pjoin(dir, f'sub-{id}', 'tracts', 'wmqlqc', 'epi')
    

    return (local.path(out) for out in [t1_align_prefix, t2_align_prefix, dwi_align_prefix,
            t1_mabsmask_prefix, t2_mabsmask_prefix, eddy_bse_betmask_prefix,
            fs_dir, fs_in_eddy, fs_in_epi,
            eddy_bse_prefix, eddy_bse_masked_prefix, eddy_epi_bse_prefix, eddy_epi_bse_masked_prefix,
            eddy_prefix, eddy_epi_prefix, 
            eddy_tract_prefix, eddy_epi_tract_prefix,
            eddy_fs2dwi_dir, epi_fs2dwi_dir,
            eddy_wmql_dir, eddy_wmqlqc_dir, epi_wmql_dir, epi_wmqlqc_dir])


def create_dirs(cases, dir):
    from os import makedirs
    from os.path import isdir
    from os.path import join as pjoin
    
    if not isdir(dir): 
        for id in cases:
            makedirs(pjoin(dir, f'sub-{id}', 'anat'))
            makedirs(pjoin(dir, f'sub-{id}', 'dwi'))
            makedirs(pjoin(dir, f'sub-{id}', 'tracts'))
            makedirs(pjoin(dir, f'sub-{id}', 'anat', 'freesurfer'))
            makedirs(pjoin(dir, f'sub-{id}', 'fs2dwi'))
            makedirs(pjoin(dir, f'sub-{id}', 'tracts', 'wmql'))
            makedirs(pjoin(dir, f'sub-{id}', 'tracts', 'wmqlqc'))

