'''
Created on Jul 24, 2017

@author: dgrewal
'''
import os
import errno
import pypeliner
from scripts import CollectMetrics

def makedirs(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def bam_postprocess(inputs, output, output_bai, markdups_metrics,
                    flagstat_metrics, tempdir):

    if not os.path.exists(tempdir):
        os.makedirs(tempdir)

    merged_bam = os.path.join(tempdir, "merged.bam")
    merge_bams(inputs, merged_bam, tempdir)

    sorted_bam = os.path.join(tempdir, "sorted.bam")
    bam_sort(merged_bam, sorted_bam, tempdir)

    os.remove(merged_bam)

    bam_markdups(sorted_bam, output, markdups_metrics, tempdir)

    os.remove(sorted_bam)

    index_bam(output, output_bai)

    flagstat_bam(output, flagstat_metrics)


def index_bam(infile, outfile):

    cmd = ['samtools','index', infile, outfile]

    pypeliner.commandline.execute(*cmd)


def flagstat_bam(infile, outfile):

    cmd = ['samtools','flagstat', infile, '>', outfile]

    pypeliner.commandline.execute(*cmd)


def merge_bams(inputs, output, tmp_dir):
    if not os.path.exists(tmp_dir):
        makedirs(tmp_dir)

    filenames = inputs.values()
    
    cmd = ['picard', '-Xmx12G', '-Xms12G',
           '-XX:ParallelGCThreads=2',
           'MergeSamFiles',
           'OUTPUT=' + output,
           'SORT_ORDER=coordinate',
           'ASSUME_SORTED=true',
           'VALIDATION_STRINGENCY=LENIENT',
           'MAX_RECORDS_IN_RAM=150000',
           'TMP_DIR='+tmp_dir
           ]
    for bamfile in filenames:
        cmd.append('I='+bamfile)
    
    pypeliner.commandline.execute(*cmd)

def bam_sort(bam_filename, sorted_bam_filename, tmp_dir):
    if not os.path.exists(tmp_dir):
        makedirs(tmp_dir)

    pypeliner.commandline.execute(
        'picard', '-Xmx12G', '-Xms12G',
        '-XX:ParallelGCThreads=2',
        'SortSam',
        'INPUT=' + bam_filename,
        'OUTPUT=' + sorted_bam_filename,
        'SORT_ORDER=coordinate',
        'VALIDATION_STRINGENCY=LENIENT',
        'TMP_DIR='+tmp_dir,
        'MAX_RECORDS_IN_RAM=150000')


def bam_markdups(bam_filename, markduped_bam_filename, metrics_filename, tmp_dir):
    if not os.path.exists(tmp_dir):
        makedirs(tmp_dir)

    pypeliner.commandline.execute(
        'picard', '-Xmx12G', '-Xms12G',
        '-XX:ParallelGCThreads=2',
        'MarkDuplicates',
        'INPUT=' + bam_filename,
        'OUTPUT=' + markduped_bam_filename,
        'METRICS_FILE=' + metrics_filename,
        'REMOVE_DUPLICATES=False',
        'ASSUME_SORTED=True',
        'VALIDATION_STRINGENCY=LENIENT',
        'TMP_DIR='+tmp_dir,
        'MAX_RECORDS_IN_RAM=150000')


def bam_collect_wgs_metrics(bam_filename, ref_genome, metrics_filename, config, tmp_dir):
    if not os.path.exists(tmp_dir):
        makedirs(tmp_dir)

    pypeliner.commandline.execute(
        'picard', '-Xmx12G', '-Xms12G',
        '-XX:ParallelGCThreads=2',
        'CollectWgsMetrics',
        'INPUT=' + bam_filename,
        'OUTPUT=' + metrics_filename,
        'REFERENCE_SEQUENCE=' + ref_genome,
        'MINIMUM_BASE_QUALITY=' + str(config['picard_wgs_params']['min_bqual']),
        'MINIMUM_MAPPING_QUALITY=' + str(config['picard_wgs_params']['min_mqual']),
        'COVERAGE_CAP=500',
        'VALIDATION_STRINGENCY=LENIENT',
        'MAX_RECORDS_IN_RAM=150000',
        'COUNT_UNPAIRED=' + ('True' if config['picard_wgs_params']['count_unpaired'] else 'False'))


def bam_collect_gc_metrics(bam_filename, ref_genome, metrics_filename, summary_filename, chart_filename, tmp_dir):
    if not os.path.exists(tmp_dir):
        makedirs(tmp_dir)

    pypeliner.commandline.execute(
        'picard', '-Xmx12G', '-Xms12G',
        '-XX:ParallelGCThreads=2',
        'CollectGcBiasMetrics',
        'INPUT=' + bam_filename,
        'OUTPUT=' + metrics_filename,
        'REFERENCE_SEQUENCE=' + ref_genome,
        'S=' + summary_filename,
        'CHART_OUTPUT=' + chart_filename,
        'VALIDATION_STRINGENCY=LENIENT',
        'MAX_RECORDS_IN_RAM=150000')


def bam_collect_insert_metrics(bam_filename, flagstat_metrics_filename, metrics_filename, histogram_filename, tmp_dir):
    if not os.path.exists(tmp_dir):
        makedirs(tmp_dir)

    # Check if any paired reads exist
    has_paired = None
    with open(flagstat_metrics_filename) as f:
        for line in f:
            if 'properly paired' in line:
                if line.startswith('0 '):
                    has_paired = False
                else:
                    has_paired = True

    if has_paired is None:
        raise Exception('Unable to determine number of properly paired reads from {}'.format(flagstat_metrics_filename))

    if not has_paired:
        with open(metrics_filename, 'w') as f:
            f.write('## FAILED: No properly paired reads\n')
        with open(histogram_filename, 'w'):
            pass
        return

    pypeliner.commandline.execute(
        'picard', '-Xmx12G', '-Xms12G',
        '-XX:ParallelGCThreads=2',
        'CollectInsertSizeMetrics',
        'INPUT=' + bam_filename,
        'OUTPUT=' + metrics_filename,
        'HISTOGRAM_FILE=' + histogram_filename,
        'ASSUME_SORTED=True',
        'VALIDATION_STRINGENCY=LENIENT',
        'MAX_RECORDS_IN_RAM=150000')


def collect_metrics(flagstat_metrics, markdups_metrics, insert_metrics,
                    wgs_metrics, samplesheet, output, sample_id):

    collmet = CollectMetrics(wgs_metrics, insert_metrics, flagstat_metrics,
                             markdups_metrics, output, sample_id)
    collmet.main()
