import os

from os import listdir
from os.path import isfile, join

import sys
import subprocess
import shlex
import datetime

today = (f"{datetime.datetime.now():%Y-%m-%d}")

import pandas as pd
import argparse
import warnings

ignore_missing_files = True

class FileSubmitter():
	'''
	Class to submit jobs localy or using qsub.
	'''
	def __init__(self, log_name, file, runnumber, dtype, odir):
		self.log_name = log_name
		self.file = file
		self.runnumber = runnumber
		self.dtype = dtype
		self.odir = odir

	def submit_locally(self):
		# Submit all jobs simultanously to processing on this machine
		print("-----------------------------------")
		warnings.warn("All files will be submitted at the same time.", UserWarning)
		answer = ""
		while (answer!="y") or (answer!="n"):
			answer = input("Are you sure you want to continue?\n[y/n]: ")
		if answer=="y":
			pass
		elif answer=="n":
			sys.exit("exiting...")
		print("sh ./analyse_file.sh {} {} {} {}".format(file, runnumber, dtype, odir))

		with open("{}.log".format(self.log_name),"wb") as out, open("{}_err.log".format(self.log_name),"wb") as err:
			p = subprocess.Popen(['/bin/zsh', "./local_analyse_file.sh",
				self.file, str(self.runnumber), self.dtype, self.odir],
				stdout=out, stderr=err)
			print("PID number for started process:\t{}".format(p.pid))

	def submit_qsub(self):
		# use qsub to submitt the files to Batch Farm

		# build the submission command. More qsub options 
		# are passed in qsub_analyse_file.sh
		#
		# Important: maximum usage of memory for each job
		# has to be large enough. This is specified using the
		# -l h_rss=8G option of qsub. If the consumed memory
		# of one job is above the requested h_rss limit, this
		# process will be killed by the batch system sending
		# an SIGKILL signal.
		submission = "qsub -o {}_output.txt -e {}_errors.txt ./qsub_analyse_file.sh {} {} {} {}".format(self.log_name, self.log_name, self.file, self.runnumber, self.dtype, self.odir)
		print(submission)
		subprocess.call(submission, shell=True)



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--listGAMMA", type=str, default=None,
						help="list of gamma files")
	parser.add_argument("--listNSB", type=str, default=None,
						help="list of NSB files")
	parser.add_argument("--submit", type=str, default="False",
						help="submit the jobs")
	parser.add_argument("--qsub", type=str, default="False",
						help="use qsub for submitting")
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

	if args.qsub in ("True", "true", "t", "yes", "y", "1"):
		use_qsub = True
	elif args.qsub in ("False", "false", "f", "no", "n", "0"):
		use_qsub = False
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

		print("List of {} files added from file {}.".format(len(files), lists[i]))

		# iterate each of the files	    
		for file in files:
			# get runnumber
			substr = file[file.find("run")+3:file.find("_cta")]
			runnumber = [int(s) for s in substr.split("_") if s.isdigit()][0]
			if dtype == "gamma":
				pass
			elif dtype == "NSB":
				substr = file[file.find("baseline")+8:file.find(".simtel")]
				runnumber = str(runnumber) + substr
			else:
				raise ValueError("dtype not gamma or NSB")

			if submit:
				# create folder for the log files
				log_dir = "{}/LOGS/{}/".format(odir, today)
				os.system("mkdir -p {}".format(log_dir))
				# using data type and runnumber for the log files
				log_name = "{}{}_run{}".format(log_dir, dtype, runnumber)

				print("-------------- start analysing next file --------------")
				print("Submitting file with runnumber {} for {}".format(runnumber, dtype))
				print("File to analyse: {}".format(file))
				print("Writing logs to {}".format(log_dir))
				# delet existing log files
				os.system("rm {}_*.txt".format(log_name))

				Submitter = FileSubmitter(log_name, file, runnumber, dtype, odir)

				if use_qsub:
					#####################
					# submit using qsub #
					#####################
					#sys.exit("...")
					Submitter.submit_qsub()
				elif not use_qsub:
					########################
					# submitt jobs locally #
					########################
					Submitter.submit_locally()

			# concatenate the single output files
			if concatenate & (not ignore_missing_files):
				# get output directory
				output_directory = "{}/{}".format(odir, dtype)
				
				# get stored dataframes
				store = pd.HDFStore('{}/image_numbers_{}_run{}.h5'
								.format(output_directory, dtype, runnumber))
				_number_images = store['number_images']
				# append all files to one DF
				number_images = number_images.append(_number_images)

		if concatenate & (not ignore_missing_files):
			store = pd.HDFStore('{}/image_numbers_{}_allruns.h5'
					.format(output_directory, dtype))
			# Save the output to HDF5 file
			store['number_images'] = number_images


		# 
		if concatenate & ignore_missing_files & (dtype=="gamma"):

			output_directory = "{}/{}".format(odir, dtype)
			# delet existing _allruns.h5 file
			os.system("rm {}/image_numbers_{}_allruns.h5".format(output_directory, dtype))

			files = [f for f in listdir(output_directory) if isfile(join(output_directory, f))]

			for file in files:
				print(file)
				store = pd.HDFStore('{}/{}'.format(output_directory, file))
				_number_images = store['number_images']
				# append all files to one DF
				number_images = number_images.append(_number_images)

			store = pd.HDFStore('{}/image_numbers_{}_allruns.h5'
					.format(output_directory, dtype))
			# Save the output to HDF5 file
			store['number_images'] = number_images