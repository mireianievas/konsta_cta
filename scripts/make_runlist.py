import sys
import os
import numpy as np
import glob
import argparse
import errno

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=str, default=None,
                        help="directory with stored files")
    parser.add_argument("--extension", type=str, default=None,
                        help="extension to search for")
    parser.add_argument("--nfiles", type=int, default=100,
                        help="number of files to select")
    parser.add_argument("--shuffle", type=bool, default=True,
                        help="shuffle before selection")
    parser.add_argument("--outname", type=str, default=".",
                        help="path output directory")
    parser.add_argument("--trainset", type=str, default="false")
    args = parser.parse_args()

    directory = args.directory
    extension = args.extension
    nfiles = args.nfiles

    if args.trainset in ["True", "true"]:
        trainset = True
    else:
        trainset = False

    if args.shuffle in ["True", "true"]:
        shuffle = True
    else:
        shuffle = False
    outname = args.outname

    if os.path.exists(outname):
        print("The file {} already exists".format(outname))

        merge = input("Overwrite file? [y/n] ")
        if merge == "y":
            pass
        elif merge == "n":
            sys.exit("exiting...")
        else:
            sys.exit("invalid option {}".format(merge))

    elif not os.path.exists(os.path.dirname(outname)):
        try:
            os.makedirs(os.path.dirname(outname))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    files = glob.glob("{}/*{}".format(directory, extension))

    if len(files) < nfiles:
        raise ValueError("Can't select more files than available."
                         "Maximum number ist {}".format(len(files)))

    if shuffle:
        np.random.shuffle(files)

    if trainset:
        files_train = files[:nfiles]
        files_test = files[nfiles:]

        np.savetxt("{}_train.list".format(outname), files_train, delimiter='\n', fmt='%s')
        np.savetxt("{}_test.list".format(outname), files_test, delimiter='\n', fmt='%s')
    else:
        if nfiles > 0:
            files = files[:nfiles]
        else:
            print("Will write list with all files")
            pass

        np.savetxt(outname, files, delimiter='\n', fmt='%s')

        print("{} files were written to {}".format(len(files), outname))
