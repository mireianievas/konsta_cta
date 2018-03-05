import sys
import argparse

from konsta_cta.readdata import FileReader
from konsta_cta.image import ImagePreparer

''' Process simtel array files for cta using cta-pipe.

In order to generate comparison plots for CTA-pipe


input:
------
--pathGAMMA 	Path to gamma files
--pathPROTON 	Path to proton files
--list		NOT PROPERLY SUPPORTED SO FAR --> readdata.py



Planned structure:
------------------
- collect all inputs
- iterate all files
	- submit (qsub)?
		- calibrate, clean, parameterisation
		- write list of all parameters to one file
'''

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--pathGAMMA", type=str, default=None,
                        help="Path to gamma files")
    parser.add_argument("--pathNSB", type=str, default=None,
                        help="Path to proton files")
    parser.add_argument("--listGAMMA", type=str, default=None,
                        help="list of gamma files")
    parser.add_argument("--listNSB", type=str, default=None,
                        help="list of proton files")
    parser.add_argument("--numTELS_ENERGY", type=bool, default=False,
                        help="Plot number of telescopes with image"
                        "after cleaning vs energy")
    args = parser.parse_args()

    list_gammas = args.listGAMMA
    list_NSB = args.listNSB
    path_gammas = args.pathGAMMA
    path_NSB = args.pathNSB

    try:
        gamma = FileReader(list_gammas, "Gamma")
    except ValueError:
        print('Now trying gnereate list from path.')
        try:
            gamma = FileReader.get_file_list(path_gammas, "Gamma")
        except IOError:
            print('No path given for gammas.')
            sys.exit('exiting...')
        except ValueError:
        	print("List is empty.")
        	sys.exit('exiting...')
	
    try:
        protons = FileReader(list_NSB, "NSB")
    except ValueError:
        print('Now trying gnereate list from path.')
        try:
            NSB = FileReader.get_file_list(path_NSB, "NSB")
        except IOError:
            print('No path given for protons.')
            sys.exit('exiting...')
        except ValueError:
        	print("List is empty.")
        	sys.exit('exiting...')

    print("Number of files for on Source: {}".format(len(gammas.file_list)))
    print("Number of files for NSB: {}".format(len(NSB.file_list)))

    if args.numTELS_ENERGY:
        pass
