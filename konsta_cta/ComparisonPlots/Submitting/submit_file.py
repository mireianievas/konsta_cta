import os

from os import listdir
from os.path import isfile, join

import sys
import subprocess
import shlex
import datetime
import pickle

today = (f"{datetime.datetime.now():%Y-%m-%d}")

import pandas as pdS
import argparse
import warnings

ignore_missing_files = False

class FileSubmitter():
	'''
	Class to submit jobs localy or using qsub.
	'''
	def __init__(self, log_name, file, runnumber, zenith, direction, dtype, odir, integrator, cleaner, tels_to_use):
		self.log_name = log_name
		self.file = file
		self.runnumber = runnumber
		self.dtype = dtype
		self.odir = odir
		self.integrator = integrator
		self.cleaner = cleaner
		self.zenith = zenith
		self.direction = direction
		self.tels_to_use = tels_to_use

	def submit_locally(self):
		# Submit all jobs simultanously to processing on this machines
		print("sh ./local_analyse_file.sh {} {} {} {} {} {}".format(
					self.file, self.runnumber, self.dtype, self.odir, self.integrator, self.cleaner))

		with open("{}.log".format(self.log_name),"wb") as out, open("{}_err.log".format(self.log_name),"wb") as err:
			p = subprocess.Popen(['/bin/zsh', "./local_analyse_file.sh",
				self.file, str(self.runnumber), self.zenith, self.direction, self.zenith_direction[1],
				self.dtype, self.odir, self.integrator, self.cleaner], stdout=out, stderr=err)
			print("PID number for started process:\t{}".format(p.pid))

	def submit_qsub(self):
		'''use qsub to submitt the files to Batch Farm

		build the submission command. More qsub options 
		are passed in qsub_analyse_file.sh
		
		Important: maximum usage of memory for each job
		has to be large enough. This is specified using the
		-l h_rss=8G option of qsub. If the consumed memory
		of one job is above the requested h_rss limit, this
		process will be killed by the batch system sending
		an SIGKILL signal.
		'''

		submission = "qsub -o {}_{}_{}_output.txt -e {}_errors.txt ./qsub_analyse_file.sh {} {} {} {} {} {} {} {} {}".format(
			self.log_name, self.integrator[:5], self.cleaner[:5], self.log_name, self.file,
			self.runnumber, self.zenith, self.direction, self.dtype,
			self.odir, self.integrator, self.cleaner, self.tels_to_use)
		print(submission)
		subprocess.call(submission, shell=True)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--listGAMMA", type=str, default=None,
						help="list of gamma files")
	parser.add_argument("--listhighNSB", type=str, default=None,
						help="list of NSB files")
	parser.add_argument("--listPROTON", type=str, default=None,
						help="list of proton files")
	parser.add_argument("--tels_to_use", type=str, default="all",
						help="list of proton files")
	parser.add_argument("--submit", type=str, default="False",
						help="submit the jobs")
	parser.add_argument("--qsub", type=str, default="False",
						help="use qsub for submitting")
	parser.add_argument("--concatenate", type=str, default="False",
						help="concatenate all outputs")
	parser.add_argument("--odir", type=str, default=".",
						help="output directory")
	parser.add_argument("--methods", type=str, default="all",
						help="output directory")

	args = parser.parse_args()
	
	odir = args.odir
	methods = args.methods
	# create folder for ouput:
	os.system("mkdir -p {}".format(odir))

	tels_to_use = args.tels_to_use

	# read the input
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

	# don't process many files locally...
	if (submit) & (not use_qsub):
		print("-----------------------------------")
		warnings.warn("All files will be submitted at the same time.", UserWarning)
		answer = ""
		while (answer!="y") or (answer!="n"):
			answer = str(input("Are you sure you want to continue?\n[y/n]: "))
			if answer=="y":
				break
			elif answer=="n":
				sys.exit("exiting...")

	# collect the input files
	lists = []
	dtypes = []
	for i, (arg, dtype) in enumerate(zip([args.listGAMMA, args.listPROTON, args.listhighNSB],["gamma", "proton", "NSB"])):
		if bool(arg) & (arg != "None"):
			lists.append(arg)
			dtypes.append(dtype)

	for i, (file_list, dtype) in enumerate(zip(lists, dtypes)):
		if concatenate:
			# generate empty DataFrame
			number_images = pd.DataFrame(columns=["Emc", "all_images", "cleaned"])

			phe_charge = {}

		# read the list of files
		with open(file_list) as f:
			files = f.read().splitlines()

		print("List of {} files added from file {}.".format(len(files), lists[i]))

		# iterate each of the files	    
		for file in files:
			# get runnumber
			substr = file[file.find("run")+3:file.find("_cta-")]

			runnumber = [int(s) for s in substr.split("_") if s.isdigit()][0]

			# get zenith angle and direction
			if (dtype == "gamma") | (dtype == "proton"):
				substr = file[file.find("/{}".format(dtype))+len(dtype)+2:file.find("run")-1]
				### for test directory uncomment for actual file!
				#substr = file[file.find("/Test/")+len(dtype)+2:file.find("run")-1]
				zen_dir = substr.split("_")[1:]
			elif dtype == "NSB":
				substr = file[file.find("/gamma")+len(dtype):file.find("run")-1]
				zen_dir = substr.split("_")[1:]


			if (dtype == "gamma") | (dtype == "proton"):
				pass
			elif dtype == "NSB":
				substr = file[file.find("baseline")+8:file.find(".simtel")]
				runnumber = str(runnumber) + substr
			else:
				raise ValueError("dtype not gamma or NSB")

			if submit:
				# create folder for the log files
				log_dir = "{}/LOGS/{}/{}/".format(odir, today, dtype)
				os.system("mkdir -p {}".format(log_dir))
				print("-------------- start analysing next file --------------")
				print("Submitting file with runnumber {} for {}".format(runnumber, dtype))
				print("File to analyse: {}".format(file))
				print("Writing logs to {}".format(log_dir))

				if methods=='all':
					integrators = ['GlobalPeakIntegrator', 'LocalPeakIntegrator', 'NeighbourPeakIntegrator', 'AverageWfPeakIntegrator']
					cleaners = ['NullWaveformCleaner', 'CHECMWaveformCleanerAverage', 'CHECMWaveformCleanerLocal']
				elif methods=='default':
					integrators = ['NeighbourPeakIntegrator']
					cleaners = ['NullWaveformCleaner']

				#loop through all methods:
				for integrator in integrators:
					for cleaner in cleaners:			
						# using data type and runnumber for the log files
						log_name = "{}{}_{}_{}_run{}_{}_{}".format(log_dir, dtype, zen_dir[0], zen_dir[1], runnumber, integrator[:4], cleaner[:4])
						# delet existing log files
						os.system("rm {}_*.txt".format(log_name))

						#if cleaner == "CHECMWaveformCleanerAverage":
						#	sys.exit("exiting...")

						Submitter = FileSubmitter(log_name, file, runnumber, zen_dir[0], zen_dir[1], dtype, odir, integrator, cleaner, tels_to_use)

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
				
				############ pixel charges ###########
				try:
					with open('{}/pixel_pe_{}_run{}.pkl'.format(
						output_directory, dtype, runnumber), 'rb') as f:
						_phe_charge = pickle.load(f)
				except:
					print('{}/pixel_pe_{}_run{}.pkl could not be loaded.'.format(
					output_directory, dtype, runnumber))

				# append everything to one dict
				for key in list(_phe_charge.keys()):
					try:
						phe_charge[key].extend(_phe_charge[key])
					except:
						print("Adding key {} to dict".format(key))
						phe_charge[key] = _phe_charge[key]


				########## number of images ##########
				# get stored dataframes
				try:
					store = pd.HDFStore('{}/image_numbers_{}_run{}.h5'
									.format(output_directory, dtype, runnumber))
					_number_images = store['number_images']
					# append all files to one DF
					number_images = number_images.append(_number_images)
				except:
					print('{}/image_numbers_{}_run{}.h5 could not be loaded.'
									.format(output_directory, dtype, runnumber))


		# save collected informations to files
		if concatenate & (not ignore_missing_files):

			############ pixel charges ###########
			with open('{}/pixel_pe_{}_allruns.pkl'.format(output_directory, dtype), 'wb') as f:
				pickle.dump(phe_charge, f, pickle.HIGHEST_PROTOCOL)


			########## number of images ##########
			store = pd.HDFStore('{}/image_numbers_{}_allruns.h5'
					.format(output_directory, dtype))
			# Save the output to HDF5 file
			store['number_images'] = number_images


		# 
		if concatenate & ignore_missing_files & (dtype=="gamma"):

			output_directory = "{}/{}".format(odir, dtype)
			############ pixel charges ###########


			########## number of images ##########
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
