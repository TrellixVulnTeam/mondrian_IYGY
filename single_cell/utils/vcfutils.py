'''
Created on Feb 27, 2018

@author: dgrewal
'''
import warnings
import biowrappers.components.io.vcf.tasks

def _get_header(infile):
    '''
    Extract header from the VCF file

    :param infile: input VCF file
    :return: header
    '''

    header = []
    for line in infile:
        if line.startswith('##'):
            header.append(line)
        elif line.startswith('#'):
            header.append(line)
            return header
        else:
            raise Exception('invalid header: missing #CHROM line')

    warnings.warn("One of the input files is empty")
    return []

def concatenate_vcf(infiles, outfile):
    '''
    Concatenate VCF files

    :param infiles: dictionary of input VCF files to be concatenated
    :param outfile: output VCF file
    '''

    with open(outfile, 'w') as ofile:
        header = None

        for _,ifile in infiles.iteritems():

            with open(ifile) as f:

                if not header:
                    header = _get_header(f)

                    for line in header:
                        ofile.write(line)
                else:
                    if not _get_header(f) == header:
                        warnings.warn('merging vcf files with mismatching headers')

                for l in f:
                    print >> ofile, l,

def merge_vcfs(infiles, outfiles, docker_config={}):
    for infile in infiles:
        biowrappers.components.io.vcf.tasks.index_vcf(infile, index_file=infile + '.tbi', docker_config=docker_config)
    biowrappers.components.io.vcf.tasks.merge_vcfs(infiles, outfiles)


