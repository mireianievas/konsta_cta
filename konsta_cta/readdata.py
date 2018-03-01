import os
from os.path import expandvars

from ctapipe.io import event_source

import warnings

class FileReader():
    ''' Simple class to generate file list and read in files

        Allows to generate a file list from given directory
        or use a list of the links to the files. This list
        can be read eather using generator or directly from
        the list.
    '''

    def __init__(self, file_list=False, datatype=None, max_events=None):

        self.max_events = max_events
        self.file_list = file_list
        self.datatype = datatype

        if not self.datatype:
            # Name of datatype should be passed
            warnings.warn("No name for datatype passed")

        if not file_list:
            raise ValueError("No list given.")
        elif len(self.file_list) == 0:
            raise Exception('No files found in "{}"'.format(
                str(self.directory)))

    # generate a list of input files from the files in directory
    @classmethod
    def get_file_list(cls, directory, datatype=None, max_events=None):
        file_list = os.popen('find ' + str(directory) +
            ' -name "*run*simtel*"').read().split('\n')[:-1]
        return cls(file_list, datatype)

    # read the sources from the file in list
    def read_files(self):
        self.sources = {}
        for i, file in enumerate(self.file_list):
            infile = expandvars(file)
            self.sources[i] = event_source(infile, max_events=self.max_events)

    # For reading the files with generator
    # read the sources as generator
    def read_files_as_generator(self, file):
        infile = expandvars(file)
        self.source = event_source(infile, max_events=self.max_events)

    # read source as generator
    def files_as_generator(self):
        for count, file in enumerate(self.file_list):
            print('Now opening file {}'.format(self.datatype, count + 1))
            yield self.read_files_as_generator(file)
