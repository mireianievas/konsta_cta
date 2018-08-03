'''
Script to read the input lists and submit the jobs to the cluster.

Currently it must be called from within the directory in which
itself, qsub_file.sh and analyse_file.py are existent.
'''

import os
import subprocess
import argparse
import glob
import json
import sys
import errno

import datetime
today = (f"{datetime.datetime.now():%Y-%m-%d}")


class FileSubmitter():
	'''
	Class to submit ctapip jobs using qsub.
	'''

	def __init__(self, file, dtype, odir, tels_to_use,
				 ctapipe_aux_dir, config):
		'''
		file 		- file to analyse (str)
		dtypes 		- datatype (str)
		odir		- output directory (str)
		tels_to_use - file with list of telescopes (str)
		config 		- json configuratino file
		'''

		self.file = file
		self.dtype = dtype
		self.ctapipe_aux_dir = ctapipe_aux_dir
		self.directory = os.getcwd()

		if odir[0] == "/":
			self.odir = odir # full path was given
		else:
			odir = self.directory + "/" + odir 

		if (tels_to_use[0] == "/") | (tels_to_use == "all"):
			self.tels_to_use = tels_to_use
		else:
			self.tels_to_use = self.directory + "/" + tels_to_use

		if config[0] == "/":
			self.config = config
		else:
			self.config = self.directory + "/" + config

		# get runnumber
		substr = file.split("/")[-1]
		substr = substr[substr.find("run") + 3:substr.find("_cta-")]
		runnumber = [int(s) for s in substr.split("_") if s.isdigit()][0]

		# get zenith angle and direction
		if (dtype == "gamma") | (dtype == "proton"):
			substr = file[file.find("/{}".format(dtype)) +
						  len(dtype) + 2:file.find("run") - 1]
			substr = substr.split("_")[1:]
			zenith = substr[0]
			direction = substr[1]

		# directiory for log files
		log_dir = "{}/LOGS/{}/{}/".format(odir, today, dtype)
		os.system("mkdir -p {}".format(log_dir))
		print("Writing logs to {}".format(log_dir))

		# name of logfile
		self.log_name = "{}{}_{}_{}_run{}".format(log_dir, dtype,
									  zenith, direction, runnumber)
		# name of outputfile
		self.outputfile = '{}/output_{}_{}_{}_run{}'.format(
						odir, dtype, zenith, direction, runnumber)

	def submit(self):
		'''
		use qsub to submit the files the submission command.
		More qsub options are passed in qsub_file.sh.
		'''

		submit = ("qsub -o {}_output.txt -e {}_errors.txt " +
				  "./qsub_file.sh {} {} {} {} {} {}").format(
			self.log_name, self.log_name, self.file,
			self.outputfile, self.tels_to_use,
			self.directory, self.ctapipe_aux_dir, self.config)
		print(submit)

		subprocess.call(submit, shell=True) # submit the job


if __name__ == '__main__':
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--listGAMMA", type=str, default=None,
						help="path to runlist for GAMMAS")
	parser.add_argument("--listPROTON", type=str, default=None,
						help="path to runlist for PROTONS")
	parser.add_argument("--odir", type=str, default=".",
						help="path output directory")
	parser.add_argument("--tels_to_use", type=str, default="all",
						help="path to list with telescope numbers \
						to use or 'all' to use full telescope list")
	parser.add_argument("--config", type=str, default="config.json",
						help="configuration file")
	args = parser.parse_args()
	
	odir = args.odir
	tels_to_use = args.tels_to_use
	config_file = args.config

	#read config
	with open(args.config) as json_file:
			config = json.load(json_file)

	available_modes = ["make_direction_LUT", "merge_LUT", "write_list_dca", "write_lists"]
	if (config["mode"] in available_modes):
		print("Skript executed in mode {}".format(config["mode"]))
	else:
		raise NotImplementedError("{} is not implemented. Possible"
			"modes are {}".format(config["mode"], available_modes))


	ctapipe_aux_dir = os.path.abspath(config["ctapipe_aux_dir"])
	
	if config["mode"] == "merge_LUT":
		from direction_LUT import *
		import numpy as np


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
		    except OSError as exc: # Guard against race condition
		        if exc.errno != errno.EEXIST:
		            raise

		file_list = glob.glob("{}/output*.json".format(odir)) # get all files
		LUTgenerator = LookupGenerator.combine_LUTs(file_list)	# combine all lookups
		LUTgenerator.save(LUTfile)
		print("Merged {} files to one LUT in {}".format(len(file_list), LUTfile))
	else:

		# collect the input files
		runlists = []
		dtypes = []
		for i, (arg, dtype) in enumerate(zip(
					[args.listGAMMA, args.listPROTON], 
					["gamma", "proton"])):
			# check which lists were given
			if bool(arg) & (arg != "None"):
				runlists.append(arg)
				dtypes.append(dtype)

		# loop over all particle types
		for runlist, dtype in zip(runlists, dtypes):
			print("Submitting next runlist:")
			print("########################")
			# read runlist
			with open(runlist) as f:
				files = f.read().splitlines()

			print("List of {} files added from file {}.".format(
				len(files), runlist))

			# loop over all files and submit each file to one job
			for file in files:
				print("-------------- staring with next file --------------")
				print("File to analyse: {}".format(file))

				Submitter = FileSubmitter(file, dtype, odir,
									tels_to_use, ctapipe_aux_dir, config_file)
				Submitter.submit()
