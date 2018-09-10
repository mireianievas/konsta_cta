import os
import subprocess
import argparse
import datetime

today = f"{datetime.datetime.now():%Y-%m-%d}"

if __name__=='__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir' , default="/lustre/fs19/group/cta/users/kpfrang/software/ctapipe_output/")
    parser.add_argument('--directories', nargs='*', required=True)
    parser.add_argument('--names', nargs='*', required=True)
    # parser.add_argument('--type', nargs='*', required=True)
    parser.add_argument('--odir', default="./AngularResolutionPlots")
    parser.add_argument('--outname', default="None")
    parser.add_argument('--offsets', nargs="*", default=[-1, 100], type=float)
    parser.add_argument('--maxfiles', type=int, default=-1)
    args = parser.parse_args()


    if args.offsets == [-1, 100]:
        odir = "{}/point".format(args.odir)
    else:
        for offset in args.offsets:
            try:
                fname += "_{}".format(offset)
            except NameError:
                fname = str(offset)

            odir = "{}/{}".format(args.odir, fname)

    directory = os.getcwd()
    if odir[0] != "/":
        odir = directory + "/" + odir

    log_dir = "{}/LOGS/{}/".format(odir, today)
    os.system("mkdir -p {}".format(log_dir))

    if len(args.names) == 2:
        if args.offsets == [-1, 100]:
            submit = "qsub -V -o {log}LOG.txt -e {log}_errors.txt ./qsub2_point.sh".format(log=log_dir)
        else:
            submit = "qsub -V -o {log}LOG.txt -e {log}_errors.txt ./qsub2.sh".format(log=log_dir)
    elif len(args.names) == 3:
        if args.offsets == [-1, 100]:
            submit = "qsub -V -o {log}LOG.txt -e {log}_errors.txt ./qsub3_point.sh".format(log=log_dir)
        else:
            submit = "qsub -V -o {log}LOG.txt -e {log}_errors.txt ./qsub3.sh".format(log=log_dir)

    for dir in args.directories:
        submit += " {}".format(dir)

    for name in args.names:
        submit += " {}".format(name)

    submit += " {}".format(args.odir)

    #for offset in args.offsets:
    #    submit += " {}".format(offset)

    submit += " {}".format(args.maxfiles)

    submit += " {}".format(directory)
    print("")
    print(submit)

    subprocess.call(submit, shell=True)