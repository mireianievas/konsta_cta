import os
from os.path import expandvars

from ctapipe.io import event_source


class FileReader():
    # Simple class to generate file list and read in files

    def __init__(self, datatype=None, directory="./", file_list=False):
        self.datatype = datatype
        self.directory = directory
        self.file_list = file_list

    # generate a list of input files from the files in directory
    def get_file_list(self):
        self.file_list = os.popen('find ' + str(self.directory) + str(
            self.datatype) + ' -name "*run*simtel*"').read().split('\n')[:-1]

        if len(self.file_list) == 0:
            raise Exception('No files found in directory "{}"'.format(
                str(self.directory) + str(self.datatype)))

    # read the files
    def read_files(self):
        if not self.file_list:
            self.get_file_list()
        print('Number of files to read: {} for datatype {}'.format(
            len(self.file_list), self.datatype))

        self.read_files_from_list()

    # read the sources from the file in list
    def read_files_from_list(self):
        self.sources = {}
        for i, file in enumerate(self.file_list):
            infile = expandvars(file)
            self.sources[i] = event_source(infile)

    # For reading the files with generator
    # read the sources as generator
    def read_files_as_generator(self, file):
        infile = expandvars(file)
        self.source = event_source(infile)

    # read source as generator
    def files_as_generator(self):
        if not self.file_list:
            self.get_file_list()
        print('Number of files to read: {} for datatype {}'.format(
            len(self.file_list), self.datatype))

        for count, file in enumerate(self.file_list):
            print('Now opening {} file {}'.format(self.datatype, count + 1))
            yield self.read_files_as_generator(file)
