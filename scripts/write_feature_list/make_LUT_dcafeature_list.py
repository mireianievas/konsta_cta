from konsta_cta.reco import LookupGenerator
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
    args = parser.parse_args()

    datadir = args.datadir


    # read config
    with open(args.config) as json_file:
        config = json.load(json_file)

    print("\nConfigurations used for this ananlysis:\n")
    print(config)

    files = glob.glob("{}/output*.h5".format(datadir))


    # LUTGen.make_lookup(config["make_direction_LUT"]["size_max"], config["make_direction_LUT"]["bins"])
    size_max = {2: 3000000,
                1: 3000000,
                0: 3000000,
                5: 3000000,
                4: 800000,
                3: 800000}

    LUTgenerator = LookupGenerator.load_data_from_files(files, size_max)
    #LUTgenerator.make_lookup(size_max, config["make_direction_LUT"]["bins"])

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
        try:
            os.makedirs(ctapipe_aux_dir)
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    LUTgenerator.save(LUTfile)
