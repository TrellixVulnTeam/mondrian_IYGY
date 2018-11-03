'''
Created on Jul 11, 2017

@author: dgrewal
'''

import pypeliner
import pypeliner.managed as mgd
from single_cell.utils import helpers
import single_cell


def create_merge_bams_workflow(
    input_bams,
    merged_bams,
    cell_ids,
    config,
    regions):

    merged_bams = dict([(region, merged_bams[region])
                         for region in regions])

    ctx = {'mem_retry_increment': 2}
    docker_ctx = helpers.get_container_ctx(config['containers'], 'single_cell_pipeline')
    ctx.update(docker_ctx)

    workflow = pypeliner.workflow.Workflow()

    workflow.setobj(
        obj=mgd.OutputChunks('cell_id'),
        value=cell_ids,
    )

    workflow.setobj(
        obj=mgd.OutputChunks('region'),
        value=regions,
    )


    workflow.transform(
        name='merge_bams',
        ctx=dict(mem=config['memory']['high'], pool_id=config['pools']['multicore'],
                 ncpus=config['max_cores'], **ctx),
        func="single_cell.workflows.merge_bams.tasks.merge_bams",
        args=(
            mgd.InputFile('bam', 'cell_id', fnames=input_bams),
            mgd.OutputFile('merged.bam', "region", fnames=merged_bams, axes_origin=[]),
            regions,
            helpers.get_container_ctx(config['containers'], 'samtools')
        ),
        kwargs = {"ncores": config["max_cores"]}
    )

    return workflow


def create_cell_region_merge_workflow(
    cell_bams,
    region_bams,
    regions,
    config,
):
    workflow = pypeliner.workflow.Workflow()

    workflow.setobj(
        obj=mgd.OutputChunks('cell_id'),
        value=cell_bams.keys(),
    )

    workflow.setobj(
        obj=mgd.OutputChunks('region'),
        value=regions,
    )

    workflow.transform(
        name='split_merge_tumour',
        func='single_cell.workflows.merge_bams.tasks.cell_region_merge_bams',
        axes=('region',),
        args=(
            mgd.InputFile('tumour_cells.bam', 'cell_id', extensions=['.bai'], fnames=cell_bams),
            mgd.OutputFile('tumour_regions.bam', 'region', axes_origin=[], extensions=['.bai'], fnames=region_bams),
            mgd.Instance('region'),
            helpers.get_container_ctx(config['containers'], 'samtools'),
        ),
    )

    return workflow

