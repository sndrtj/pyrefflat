class Exon(object):
    """
    This class defines an exon inside a record
    """
    def __init__(self, gene, transcript, chr, start, stop, n):
        self._gene = gene
        self._transcript = transcript
        self._chr = chr
        self._start = start
        self._end = stop
        self._number = n

    @property
    def gene(self):
        return self._gene

    @property
    def transcript(self):
        return self._transcript

    @property
    def chr(self):
        return self._chr

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._end

    @property
    def number(self):
        return self._number

    @classmethod
    def fromrecord(cls, record):
        exons = []
        for i, (s, e) in enumerate(zip(record.exonStarts,
                                       record.exonEnds)):
            exons.append(Exon(record.gene, record.transcript,
                              record.chromosome, s, e, i))
        return exons


class Transcript(object):
    def __init__(self, name, gene, start, end, cds_start, cds_end, exons=None):
        self.name = name
        self.gene = gene
        self.start = start
        self.end = end
        self.cds_start = cds_start
        self.cds_end = cds_end
        self.exons = exons

    def update_exons(self, exon):
        if exon.start < self.start:
            raise ValueError("Start of exon cannot be in front of start of transcript")
        if exon.end < self.end:
            raise ValueError("End of exon cannot be behind end of transcript")

        if self.exons:
            self.exons.append(exon)
        else:
            self.exons = [exon]


class Gene(object):
    def __init__(self, name, start=None, end=None, transcripts=None):
        self.name = name
        self.start = start
        self.end = end
        self.transcripts = transcripts

    def update_transcripts(self, transcript):
        if self.start:
            if transcript.start < self.start:
                self.start = transcript.start
        else:
            self.start = transcript.start

        if self.end:
            if transcript.end > self.end:
                self.end = transcript.end
        else:
            self.end = transcript.end

        if self.transcripts:
            self.transcripts += [transcript]
        else:
            self.transcripts = [transcript]
