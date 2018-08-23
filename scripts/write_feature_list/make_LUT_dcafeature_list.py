"""
Script to create LUT from dca feature list written out e.g. when executing
the main script in method write_list_dca. Required parameters are datadir
which is the path to the directory with the lists with names 'output*.h5'.
The name of the output directory is given in the configuration file specified
with --config. Additional parameters like the number of bins are also given
in this file.
For diffuse simulations, it might be necessary to produce the
LUTs in different offangle bins. Using the option "diffuse" for --offangles
allows to set bins in offangles. The on json based load method in defined in
konsta_cta.reco.LookupGenerator currently is only able to load basic LUTs
but not the "diffuse" LUTs with multiple off angle bins. Therefor
"""

from konsta_cta.reco import LookupGenerator, DiffuseLUT
import glob
import json
import sys
import os
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--datadir", type=str, default=None,
                        help="directory with the feature list stored")
    parser.add_argument("--config", type=str, default="config.json",
                        help="configuration file")
    parser.add_argument("--offangles", type=str, default="point")
    args = parser.parse_args()

    datadir = args.datadir


    # read config
    with open(args.config) as json_file:
        config = json.load(json_file)

    print("\nConfigurations used for this ananlysis:\n")
    print(config)

    files = glob.glob("{}/output*.h5".format(datadir))

    size_max = config["make_direction_LUT"]["size_max"]
    nbins = config["make_direction_LUT"]["bins"]

    ctapipe_aux_dir = os.path.abspath(config["ctapipe_aux_dir"])
    LUTfile = "{}/{}".format(ctapipe_aux_dir, config["Preparer"]["DirReco"]["LUT"])

    if os.path.exists(LUTfile):
        print("The file {} already exists".format(LUTfile))

        merge = input("Overwrite file? [y/n] ")
        if merge == "y":
            pass
        elif merge == "n":
            sys.exit("exiting...")
        else:
            sys.exit("invalid option {}".format(merge))

    elif not os.path.isdir(ctapipe_aux_dir):
        os.makedirs(ctapipe_aux_dir)

    if args.offangles == "point":
        LUTgenerator = LookupGenerator.load_data_from_files(files, size_max, nbins=nbins)
        LUTgenerator.save(LUTfile)

    elif args.offangles == "diffuse":
        off_bins = [[0, 2],
                    [2, 4],
                    [4, 6],
                    [6,10]]
        DiffLUT = DiffuseLUT.look_up_offbins(files, size_max, nbins=nbins, off_bins=off_bins)
        DiffLUT.save_pickle(LUTfile)