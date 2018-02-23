import os
from os.path import expandvars

from ctapipe.io import event_source

class FileReader():
    # Simple class to generate list of files and to read those  
    def __init__(self, datatype=None, directory="./", file_list=False):
        self.datatype = datatype
        self.directory = directory
        self.file_list = file_list
#        self.read_files()
        
    def get_file_list(self):
        # generate a list of input files from the files in directory
        self.file_list = os.popen('find '+str(self.directory)+str(self.datatype)+
                                  ' -name "*run*simtel*"').read().split('\n')[:-1]
        if len(self.file_list)==0:
            raise Exception('No files found in directory "{}"'.format(
                str(self.directory)+str(self.datatype)))

        return(self.file_list)
    
    
    def read_files_from_list(self):
        # read the sources from the file in list
        self.sources = {}
        for i, file in enumerate(self.file_list):
            infile = expandvars(file)
            self.sources[i] = event_source(infile)
        return(self.sources)
    

    def read_files(self):
        # read the files
        if not self.file_list:
            self.get_file_list()
        self.read_files_from_list()