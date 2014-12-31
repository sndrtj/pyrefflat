__author__ = 'ahbbollen'

import argparse
import math
import vcf
import json

import parser as refparser

def _calc_gqx(record, sample):
    """
    This function calculates gqx values
    GQX = min(GQ, QUAL)
    :param record: a pyvcf record
    :param sample: string containing the sample
    return: float of gqx (or gq if QUAL doesnt exist)
    """
    gq = float(record.genotype(sample)['GQ'])
    if record.QUAL is not None:
        qual = float(record.QUAL)
        return min(gq, qual)
    else:
        return gq

def _get_coverage(reader, exon, gqx, min_val, perc, sample):
    """
    This function gets coverage for an exon
    :param reader: a pyvcf Reader object
    :param exon: a pyrefflat Exon object
    :param gqx: Boolean whether to output gqx values
    :param min_gqx: mimimal value, gqx or dp, (only combined with perc)
    :param perc: Boolean whether to output attained percentage of min_gqx
    :param sample: String with sample to be queried
    return: float with coverage
    """
    try:
        records = reader.fetch(str(exon.chr), int(exon.start), int(exon.stop))
    except ValueError:
        return 0.0

    if len(records) == 0:
        return 0.0

    covs = []
    for record in records:
        if gqx:
            val = _calc_gqx(record, sample)
        else:
            val = record.genotype(sample)['DP']
        covs.append(val)

    covs = map(float, covs)
    if not perc:
        return sum(covs)/len(covs)
    else:
        passes = [x for x in covs if x >= min_val]
        percentage = (float(len(passes))/float(len(covs))) * 100
        return percentage

def asBedgraph(inputf, outputf, reff, mode, gqx, min_val, perc):
    vcfReader = vcf.Reader(filename=inputf)
    bedWriter = open(outputf, 'wb')
    refReader = open(reff, 'rb')

    for sample in vcfReader.samples:
        trackline = "track type=bedGraph name='{0}' description='gVCFCoverage' graphType='bar'".format(sample)
        bedWriter.write(bytes(trackline + "\n"))
        for line in refReader:
            record = refparser.Record(line, reff)
            for exon in record.exons:
                cov = _get_coverage(vcfReader, exon, gqx, min_val, perc, sample)
                bedline = [exon.chr, exon.start, exon.stop]
                bedline.append(cov)
                bedline = map(str, bedline)
                bedWriter.write(bytes("\t".join(bedline) + "\n"))

    bedWriter.close()
    refReader.close()

def asCSV(inputf, outputf, reff, sep, mode, gqx, min_val, perc):
    vcfReader = vcf.Reader(filename=inputf)
    bedWriter = open(outputf, 'wb')
    refReader = open(reff, 'rb')

    for sample in vcfReader.samples:
        headerline = "Sample {0}; Gene \t Transcript \t Chr \t Exon number \t Exon start \t Exon stop \t Coverage \n".format(sample)
        bedWriter.write(bytes(headerline))

        for line in refReader:
            record = refparser.Record(line, reff)
            gene = record.gene
            transcript = record.transcript
            for exon in record.exons:
                chr = exon.chr
                start = exon.start
                stop = exon.stop
                n = exon.number
                line = [gene, transcript, chr, n, start, stop]
                cov = _get_coverage(vcfReader, exon, gqx, min_val, perc, sample)
                line.append(cov)
                line = map(str, line)
                bedWriter.write(bytes(sep.join(line) + "\n"))

    bedWriter.close()
    refReader.close()


def asJSON(inputf, outputf, reff, mode, gqx, min_val, perc):
    vcfReader = vcf.Reader(filename=inputf)
    jsonWriter = open(outputf, 'wb')
    refReader = open(reff, 'rb')

    jdict = {}

    for sample in vcfReader.samples:
        for line in refReader:
            record = refparser.Record(line, reff)
            gene = record.gene
            transcript = record.transcript
            transcriptdict = {}
            for exon in record.exons:
                chr = exon.chr
                start = exon.start
                stop = exon.stop
                n = exon.number
                coverage = _get_coverage(vcfReader, exon, gqx, min_val, perc, sample)
                exondict = {"chr": chr, "start": int(start), "stop" : int(stop), "number": n, "coverage" : coverage, 'sample': sample}
                transcriptdict[n] = exondict

            try:
                jdict[gene][transcript] = transcriptdict
            except KeyError:
                jdict[gene] = {}
                jdict[gene][transcript] = transcriptdict

    jsonWriter.write(json.dumps(jdict, indent=4, sort_keys=True))
    jsonWriter.close()
    refReader.close()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    #generic arguments
    parser.add_argument('-I', '--input', help="Your input gzipped gVCF")
    parser.add_argument('-O', '--output', help="Path to output file")
    parser.add_argument('-R', '--refflat', help="Path to refflat file")
    parser.add_argument('-m', '--mode', choices=['BP_RESOLUTION', 'GVCF'], help="gVCF mode")
    parser.add_argument('-om', '--output-mode', choices=['bedgraph', 'csv', 'json'], help="Output file type")

    # optional arguments
    parser.add_argument('--tab-delimited', action='store_true', help='Output CSV as TSV')
    parser.add_argument('-g', '--gqx', action='store_true', help="Output gqx values")
    parser.add_argument('p', '--perc', action='store_true', help="Output % of --min-value")

    # other arguments
    parser.add_argument('--min-value', nargs='?', const=0, type=int, help="minimal value, in gqx or dp, defaults to 0")

    args = parser.parse_args()

    if args.output_mode == 'bedgraph':
        asBedgraph(args.input, args.output, args.refflat, args.mode, args.gqx, args.min_value, args.perc)
    elif args.output_mode == 'csv':
        if args.tab_delimited:
            sep = "\t"
        else:
            sep = ","
        asCSV(args.input, args.output, args.refflat, sep, args.mode, args.gqx, args.min_value, args.perc)
    elif args.output_mode == 'json':
        asJSON(args.input, args.output, args.refflat, args.mode, args.gqx, args.min_value, args.perc)

