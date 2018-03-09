import os
import sys
import subprocess
import shlex
import datetime

today = (f"{datetime.datetime.now():%Y-%m-%d}")

import pandas as pd
import argparse

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--listGAMMA", type=str, default=None,
						help="list of gamma files")
	parser.add_argument("--listNSB", type=str, default=None,
						help="list of NSB files")
	parser.add_argument("--submit", type=str, default="False",
						help="submit the jobs")
	parser.add_argument("--concatenate", type=str, default="False",
						help="concatenate all outputs")
	parser.add_argument("--odir", type=str, default=".",
						help="output directory")

	args = parser.parse_args()
	
	odir = args.odir
	# create folder for ouput:
	os.system("mkdir -p {}".format(odir))

	if args.submit in ("True", "true", "t", "yes", "y", "1"):
		submit = True
	elif args.submit in ("False", "false", "f", "no", "n", "0"):
		submit = False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')

	if args.concatenate in ("True", "true", "t", "yes", "y", "1"):
		concatenate = True
	elif args.concatenate in ("False", "false", "f", "no", "n", "0"):
		concatenate = False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')

	if submit & concatenate:
		raise ValueError("submit and concatenate not executable at same time")

	# collect the inputs
	lists = []
	dtypes = []
	for i, (arg, dtype) in enumerate(zip([args.listGAMMA, args.listNSB],["gamma", "NSB"])):
		if bool(arg) & (arg != "None"):
			lists.append(arg)
			dtypes.append(dtype)

	for file_list, dtype in zip(lists, dtypes):
		if concatenate:
			# generate empty DataFrame
			number_images = pd.DataFrame(columns=["Emc", "all_images", "cleaned"])
		# read the list of files
		with open(file_list) as f:
			files = f.read().splitlines()

		print("List of {} files added from file {}.".format(len(files), args.listGAMMA))

		# iterate each of the files	    
		for file in files:
			# get runnumber
			substr = file[file.find("run")+3:file.find("_cta")]
			runnumber = [int(s) for s in substr.split("_") if s.isdigit()][0]

			if submit:
				# create folder for the log files
				log_dir = "{}/LOGS/{}/".format(odir, today)
				os.system("mkdir -p {}".format(log_dir))
				# using data type and runnumber for the log files
				log_name = "{}/{}_run{}".format(log_dir, dtype, runnumber)
				# delet existing log files
				os.system("rm {}*.log".format(log_name))

				print("-------------- start analysing next file --------------")
				print("Submitting file with runnumber {} for {}".format(runnumber, dtype))
				print("File to analyse: {}".format(file))
				print("Writing logs to {}".format(log_dir))

				#####################
				# submit using qsub #
				#####################
				#print("qsub -P cta -js X_9 -l h_rt=18:00:00 -l h_rss=4G -o {}_output.txt -e {}_errors.txt ./analyse_file.sh {} {} {} {}".format(log_name, log_name, file, runnumber, dtype, odir))
				#subprocess.call("qsub -l h_rt=18:00:00 -l h_rss=4G -o {}_output.txt -e {}_errors.txt ./analyse_file.sh {} {} {} {}".format(log_name, log_name, file, runnumber, dtype, odir))

				########################
				# submitt jobs locally #
				########################
				print("sh ./analyse_file.sh {} {} {} {}".format(file, runnumber, dtype, odir))
				with open("{}.log".format(log_name),"wb") as out, open("{}_err.log".format(log_name),"wb") as err:
					p = subprocess.Popen(['/bin/sh', "./analyse_file.sh", file, str(runnumber), dtype, odir], stdout=out, stderr=err)
					print("PID number for started process:\t{}".format(p.pid))

			# concatenate the single output files
			if concatenate:
				# get output directory
				output_directory = "{}/{}".format(odir, dtype)

				# get stored dataframes
				store = pd.HDFStore('{}/image_numbers_{}_run{}.h5'
								.format(output_directory, dtype, runnumber))
				_number_images = store['number_images']
				# append all files to one DF
				number_images = number_images.append(_number_images)

		if concatenate:
			store = pd.HDFStore('{}/image_numbers_{}_allruns.h5'
					.format(output_directory, dtype))
			# Save the output to HDF5 file
			store['number_images'] = number_images