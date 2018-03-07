''' To do:
- enable a single file containing a filelist as input
'''


import warnings
import os
from os.path import expandvars

from ctapipe.io import event_source

class FileReader():
    ''' Simple class to generate file list and read in files

        Allows to generate a file list from given directory
        or use a list of the links to the files. This list
        can be read eather using generator or directly from
        the list.
    '''

    def __init__(self, file_list=None, datatype=None, max_events=None):

        self.max_events = max_events
        self.file_list = file_list
        self.datatype = datatype

        if not self.datatype:
            warnings.warn("No name for datatype passed.")

        if not self.file_list:
            raise ValueError("No list given.")
        else:
            print("Found list of {} files for datatype {}."
                .format(len(self.file_list), self.datatype))

    # generate a list of input files from the files in directory
    @classmethod
    def get_file_list(cls, directory=None, datatype=None, max_events=None):
        if not directory:
            raise IOError("No directory given")
        file_list = os.popen('find ' + str(directory) +
            ' -name "*run*simtel*"').read().split('\n')[:-1]
        return cls(file_list, datatype, max_events)

    # read the sources from the file in list
    def read_files(self, files):
        #self.source = {}
        try:
            for i, file in enumerate(files):
                infile = expandvars(file)
                self.source = event_source(infile, max_events=self.max_events)
        except:
            infile = expandvars(files)
            self.source = event_source(infile, max_events=self.max_events)

    # For reading the files with generator
    # read the sources as generator
    def read_files_as_generator(self, file):
        infile = expandvars(file)
        self.source = event_source(infile, max_events=self.max_events)

    # read source as generator
    def files_as_generator(self):
        for count, file in enumerate(self.file_list):
            print('Now opening file {} for {}'
                .format(count + 1, self.datatype))
            yield self.read_files_as_generator(file)
