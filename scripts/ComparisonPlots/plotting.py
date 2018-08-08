import os
import argparse
import sys

import numpy as np
import pandas as pd
from tables import *
import pickle

from plot_numTELSvsENERGY import plot_numTELSvsENERGY
from plot_charge_distributions import plot_charge_distributions, compare_all_methods
from plot_hillas import plot_hillas

import pickle

def check_read_files(total_files, files):
	"""
	Check if number of read files equals the total number
	of tiles to read.
	"""
	if (total_files == files):
		print("Successfully loaded all {} files.".format(files))
	else:
		print("Only {} of {} files could be loaded"
			.format(files, total_files))
		
		answer = ""
		while (answer!="y") or (answer!="n"):
			answer = str(input("Do you want to continue?\n[y/n]: "))
			if answer=="y":
				break
			elif answer=="n":
				sys.exit("exiting...")

def read_histos(directory="./HistEventDisplay/", dtype="gamma"):
	'''
	Read all histograms stored in the ascii files in directory/dtype
	and write them in the data frame. The files should contain the
	columns 'bins', 'hist', 'width'.
	'''
	files = os.popen('find '+directory+dtype+'// -name "*"').read().split('\n')[1:-1]
	# set up template dataframe
	df = pd.DataFrame()
	#name_df = []
	for file in files:
		name = file[file.find("//")+2:-4]
		onedf = pd.read_csv(file, sep=" ", names=["bins", "hists", "width"])
		onedf = onedf.append(onedf.iloc[0])
		onedf = onedf.sort_values("bins")
		onedf = onedf.reset_index(drop=True)
		onedf.loc[1:,"bins"] = onedf.loc[1:,"bins"] + onedf.loc[0,"width"]
		onedf.columns = [[name]*3, ["bins", "hists", "width"]]
		df = pd.concat([df, onedf], axis=1)
	return df


def read_histos_with_errors(directory="./HistEventDisplay/", dtype="gamma"):
	'''
	Read all histograms stored in the ascii files in directory/dtype
	and write them in the data frame. The files should contain the
	columns 'bins', 'hist', 'width'.
	'''
	files = os.popen('find '+directory+dtype+'// -name "*"').read().split('\n')[1:-1]
	# set up template dataframe
	df = pd.DataFrame()
	#name_df = []
	for file in files:
		name = file[file.find("//")+2:-4]
		onedf = pd.read_csv(file, sep=" ", names=["bins", "hists", "width", "error"])
		onedf = onedf.append(onedf.iloc[0])
		onedf = onedf.sort_values("bins")
		onedf = onedf.reset_index(drop=True)
		onedf.loc[1:,"bins"] = onedf.loc[1:,"bins"] + onedf.loc[0,"width"]
		onedf.columns = [[name]*4, ["bins", "hists", "width", "error"]]
		df = pd.concat([df, onedf], axis=1)
	return df


def rebin(bins, hist, binwidth, limits=None, numbins=40):
	'''
	Method to rebin histograms according to the limits amd mumber
	of bins specified. The output histogram might vary in limits
	from the requested values due to the finite binwidth of the
	initial histogram as the new binwidth can only be a multiples
	of the initial one. Note that this method works best with small
	initial binwidths and if the range of the original histogram
	exceeds the requested limits.
	Input
	-----
	bins - initial start each bin
	hist - bin contents
	binwidth - width of the initial bins
	limits - range for new histogram
	numbins - number of bins in new histogram

	Returns
	-------
	new_bins - new start of each bin
	new_hist - bin content of new histogram
	'''
	xmin = np.min(bins)
	xmax = np.max(bins)
	if not limits:
		limits=(xmin, xmax)
	
	# get true startpoint
	if (limits[0] < np.min(bins)) | (limits[0] > np.max(bins)):
		raise ValueError("limits not included in range of bins")
	
	if np.any(limits[0] == bins):
		start = limits[0]
	else:
		start = np.max(bins[bins < limits[0]])
		
	reqeusted_width = (limits[1] - start) / numbins
	to_merge = math.ceil(reqeusted_width / binwidth)
	
	new_binwidth = to_merge * binwidth
	stop = new_binwidth * numbins + start
	
	if (np.max(bins + binwidth) < stop):
		raise ValueError("calculated value for stop outside of range of bins")
	if np.mod(reqeusted_width, binwidth) == 0.:
		pass
	else:
		# set reqeusted_width to mutiple of binwidth which is closest to desired value.
		warnings.warn("Reqeusted width of {} not possible with given binwidth."
					  " Will use closest possible value {} instead".format(
					  np.round(reqeusted_width, 5), np.round(binwidth*to_merge, 5)))
	
	new_bins = bins[bins >= start][0:to_merge*numbins:to_merge]
	#new_bins = np.append(new_bins, np.max(new_bins) + new_binwidth)
	_hist = hist[bins >= start][0:to_merge*numbins]
	new_hist = np.zeros(40)
	for i in range(to_merge):
		new_hist = np.sum([new_hist, _hist[i::to_merge]], axis=0)
	# adapt for plotting:
	new_bins = np.append(new_bins, np.max(new_bins) + new_binwidth)
	new_hist = np.append(new_hist[0], new_hist)
	
	return new_bins, new_hist

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("--datadir", type=str, default="./Analysis",
						help="maximum number of events per file")
	parser.add_argument("--odir", type=str, default="./Plots",
						help="maximum number of events per file")
	parser.add_argument("--numTELS_ENERGY", type=str, default="False",
						help="Plot number of telescopes with image"
						"after cleaning vs energy")
	parser.add_argument("--charge_distributions", type=str, default="False",
						help="Plot number of telescopes with image"
						"after cleaning vs energy")
	parser.add_argument("--hillas", type=str, default="False",
						help="Plot hillas parameters")
	parser.add_argument("--direction", type=str, default="all",
						help="direction to considere for plot")
	parser.add_argument("--EventDisplayDir", type=str, default="None",
						help="directory containing extracted histograms as ascii file")
	parser.add_argument("--MARSDir", type=str, default="None",
						help="directory containing extracted histograms as ascii file")

	args = parser.parse_args()

	if args.numTELS_ENERGY in ("True", "true", "t", "yes", "y", "1"):
		numTELS_ENERGY = True
	elif args.numTELS_ENERGY in ("False", "false", "f", "no", "n", "0"):
		numTELS_ENERGY = False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')

	if args.charge_distributions in ("True", "true", "t", "yes", "y", "1"):
		charge_distributions = True
	elif args.charge_distributions in ("False", "false", "f", "no", "n", "0"):
		charge_distributions = False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')


	if args.hillas in ("True", "true", "t", "yes", "y", "1"):
		hillas = True
	elif args.hillas in ("False", "false", "f", "no", "n", "0"):
		hillas = False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')

	if args.direction in ("all", "ALL", "All"):
		direction = "*"
	elif args.direction in ("s", "south", "0", "0deg"):
		direction = "0deg"
	elif args.direction in ("n", "north", "180", "180deg"):
		direction = "1800deg"

	EDdir = args.EventDisplayDir
	MARSDir = args.MARSDir

	if EDdir=="./HistEventDisplay/hyperarray/":
		hyp_stand = "hyper"
		ED = True
	elif EDdir=="./HistEventDisplay/standardarray/":
		hyp_stand = "standard"
		ED = True
	else:
		hyp_stand=""
		ED = False


	odir = args.odir
	# creat ouput directory
	os.system("mkdir -p {}".format(odir))
	datadir = args.datadir

	#################################################################################
	#################################################################################

	## only use specific runnumbers for hyperarray
	#if EDdir=="./HistEventDisplay/hyperarray/":
	#	with open("./Runlist_Elisa/runnum_gamma.dat") as f:
	#		runnumber_gamma = f.read().splitlines()
	#	with open("./Runlist_Elisa/runnum_proton.dat") as f:
	#		runnumber_proton = f.read().splitlines()


	# read the EventDisplay outputs
	ED_gamma = read_histos(directory=EDdir, dtype="gamma")
	ED_proton = read_histos(directory=EDdir, dtype="proton")

	# raw data without image cleaning
	ED_gamma_raw = read_histos(directory=EDdir, dtype="raw/gamma")
	ED_proton_raw = read_histos(directory=EDdir, dtype="raw/proton")

	# data with errors
<<<<<<< HEAD
	ED_gamma_err = read_histos_with_errors(directory=EDdir, dtype="with_err/gamma_new_tubes")
	######### no data for protons.
	ED_proton_err = read_histos_with_errors(directory=EDdir, dtype="with_err/gamma_new_tubes")
=======
	ED_gamma_err = read_histos_with_errors(directory=EDdir, dtype="with_err/gamma")
	ED_proton_err = read_histos_with_errors(directory=EDdir, dtype="with_err/gamma")
>>>>>>> 507fdcf53c4464f4822d763ecffe7109305ed0d6

	###### select which EventDisplay output to use here:
	if EDdir=="./HistEventDisplay/hyperarray/":
		ED_output = [ED_gamma_err, ED_proton_err, None]
		witherr = True
	elif EDdir=="./HistEventDisplay/standardarray/":
		ED_output = [ED_gamma, ED_proton, None]
		witherr = False

	# read dict with tel_id --> Cameratype
	with open('tel_list.pickle', 'rb') as handle:
		tel_list = pickle.load(handle)

	# read MARS output
	MARS_gamma = pd.read_csv("{}/tuple_0.txt".format(MARSDir), sep=";", header=0)
	MARS_gamma = MARS_gamma.append(
				pd.read_csv("{}/tuple_180.txt".format(MARSDir), sep=";", header=0),
				ignore_index=True)
	
	# draw sample as was build for 55 files:
	MARS_gamma = MARS_gamma.sample(frac=50/55)

	MARS_gamma = MARS_gamma[MARS_gamma.numUsedPix > 0]
	# add Cameras
	MARS_gamma.telID = MARS_gamma.telID.astype(int)
	MARS_gamma["camera"] = [tel_list[x] for x in MARS_gamma.telID]

	MARS_gamma["core_dist"] = np.sqrt(MARS_gamma.coreX**2 + MARS_gamma.coreY**2) / 100
	MARS_gamma["Emc_log"] = np.log10(MARS_gamma.Etrue / 1000) # E is in MeV

	charge_dist = {}
	charge_dist["gamma"] = {}
	charge_dist["proton"] = {}

	if charge_distributions:
		integrators = ['GlobalPeakIntegrator', 'LocalPeakIntegrator',
					   'NeighbourPeakIntegrator', 'AverageWfPeakIntegrator']
	else:
		integrators = ['NeighbourPeakIntegrator']

	for integrator in integrators:
	#for integrator in ['GlobalPeakIntegrator']:
		if (hillas | numTELS_ENERGY) & charge_distributions:
			raise AttributeError("Option charge_distributions not valid with other options.")
		elif hillas | numTELS_ENERGY:
			cleaners = ['NullWaveformCleaner']
		elif charge_distributions:
			cleaners = ['NullWaveformCleaner', 'CHECMWaveformCleanerAverage',
						'CHECMWaveformCleanerLocal']

		for cleaner in cleaners:
			charges = None
			print("Now at integrator {} and cleaner {}".format(integrator, cleaner))


			#####################
			# Hillas Parameters #
			#####################

			if (hillas):
				print("-----------------")
				print("hillas parameters")
				print("-----------------")
				print("Starting with integrator {} and cleaner {}".format(integrator, cleaner))
				file_list_gamma = os.popen('find {}/gamma/ -name "hillas_gamma_20deg_{}_run*_{}_{}.h5"'
						.format(datadir, direction, integrator, cleaner)).read().split('\n')[:-1]


				#file_list_proton = os.popen('find {}/proton/ -name "hillas_proton_20deg_{}_run*_{}_{}.h5"'
				#		.format(datadir, direction, integrator, cleaner)).read().split('\n')[:-1]
				#only gammas for plot mit MARS
				file_list_proton = []


				file_list_highNSB = os.popen('find {}/NSB/ -name "hillas_NSB_20deg_{}_run*_{}_{}.h5"'
						.format(datadir, direction, integrator, cleaner)).read().split('\n')[:-1]

				for file_list, EventDisplay, MARS, dtype in zip([file_list_gamma, file_list_proton, file_list_highNSB],
														ED_output, [MARS_gamma, None, None],
														["gamma", "proton", "highNSB"]):

					if len(file_list)==0:
						continue
					else:
						hillas_df = None

						#print("Try to load {} {} files for number of image"
						#	  " plot".format(len(file_list), dtype))
						n = 0
						for file in file_list:
							"""
							if EDdir=="./HistEventDisplay/hyperarray/":
								hyp_stand = "hyper"
								#runnumber = file[file.find("_run")+4:file.find(integrator)-1]
								#if dtype=="gamma":
								#	number_of_files = len(runnumber_gamma)
								#	if runnumber in runnumber_gamma:
								#		pass
								#	else:
								#		continue
								#elif dtype=="proton":
								#	number_of_files = len(runnumber_proton)
								#	if runnumber in runnumber_proton:
								#		pass
								#	else:
								#		continue
							else:
								hyp_stand = "standard"
							"""
							number_of_files = len(file_list)
							
							number_of_files = len(file_list)

							if ((n % 10) == 0):
								print("Will read file {} of {} for {}.".format(n+1, number_of_files, dtype))
							try:
								store = pd.HDFStore(file)
								hillas_df = hillas_df.append(store['hillas'], ignore_index=True)
								store.close()
								n += 1
							except (NameError, AttributeError):
								hillas_df = store['hillas']
								store.close()
								n += 1
							except KeyError:
								print("File {} not found".format(file))
							except:
								print("Error at file {}".format(file))

						check_read_files(number_of_files, n)

						compare_directory = "{}/{}/hillas/ED_compare/{}/{}".format(odir, dtype, integrator, cleaner)
						output_directory = "{}/{}/hillas/{}/{}".format(odir, dtype, integrator, cleaner)
						#create output directory
						os.system("mkdir -p {}".format(output_directory))

						os.system("mkdir -p {}".format(compare_directory))

						plot_hillas(hillas_df, EventDisplay, MARS, tel_list, "{}/Images"
							.format(output_directory), "{}/Images"
							.format(compare_directory), hyp_stand, ED, witherr)

			#################
			# Number Images #
			#################

			if (numTELS_ENERGY):
				print("-------------")
				print("number images")
				print("-------------")
				file_list_gamma = os.popen('find {}/gamma/ -name "image_numbers_gamma_20deg_{}_run*_{}_{}.h5"'
						.format(datadir, direction, integrator, cleaner)).read().split('\n')[:-1]


				file_list_proton = os.popen('find {}/proton/ -name "image_numbers_proton_20deg_{}_run*_{}_{}.h5"'
						.format(datadir, direction, integrator, cleaner)).read().split('\n')[:-1]

				number_images = None
				for file_list, EventDisplay, EventDisplay_raw, dtype in zip(
					[file_list_gamma, file_list_proton], [ED_gamma, ED_proton],
					[ED_gamma_raw, ED_proton_raw], ["gamma", "proton"]):

#					print("Try to load {} {} files for number of image"
#						  " plot".format(len(file_list), dtype))
					n = 0
					for file in file_list:

						number_of_files = len(file_list)


						if ((n % 10) == 0):
							print("Will read file {} of {} for {}.".format(n+1, number_of_files, dtype))
						try:
							store = pd.HDFStore(file)
							number_images = number_images.append(store['number_images'])
							store.close()
							n += 1
						except (NameError, AttributeError):
							number_images = store['number_images']
							print("Starting with integrator {} and cleaner {}"
									.format(integrator, cleaner))
							store.close()
							n += 1
						except KeyError:
							print("File {} not found".format(file))
						except:
							print("Error at file {}".format(file))


					check_read_files(number_of_files, n)

					compare_directory = "{}/{}/image_reconstruction/ED_compare/{}/{}".format(odir, dtype, integrator, cleaner)
					output_directory = "{}/{}/image_reconstruction/{}/{}".format(odir, dtype, integrator, cleaner)
					#create output directory

					os.system("mkdir -p {}".format(output_directory))
					os.system("mkdir -p {}".format(compare_directory))
					
					plot_numTELSvsENERGY(number_images, EventDisplay, EventDisplay_raw, "{}/Images"
						.format(output_directory), "{}/Images"
						.format(compare_directory), hyp_stand)
			
			
			########################
			# Charge distributions #
			########################

			if (charge_distributions):

				print("--------------------")
				print("Charge distribitions")
				print("--------------------")
				# dict to combine complete input in

				file_list_gamma = os.popen('find {}/gamma/ -name "pixel_pe_gamma_20deg_{}_run*_{}_{}.pkl"'
						.format(datadir, direction, integrator, cleaner)).read().split('\n')[:-1]

				file_list_proton = os.popen('find {}/proton/ -name "pixel_pe_proton_20deg_{}_run*_{}_{}.pkl"'
						.format(datadir, direction, integrator, cleaner)).read().split('\n')[:-1]

				

				for file_list, dtype in zip([file_list_gamma, file_list_proton], ["gamma", "proton"]):
				
					print("Try to load {} {} files for charge distirbutions"
						  " plot".format(len(file_list), dtype))

					hist = {}
					charges = None
					n = 0
					for file in file_list:
						"""
						if EDdir=="./HistEventDisplay/hyperarray/":
							hyp_stand = "hyper"
							#runnumber = file[file.find("_run")+4:file.find(integrator)-1]
							#if dtype=="gamma":
							#	number_of_files = len(runnumber_gamma)
							#	if runnumber in runnumber_gamma:
							#		pass
							#	else:
							#		continue
							#elif dtype=="proton":
							#	number_of_files = len(runnumber_proton)
							#	if runnumber in runnumber_proton:
							#		pass
							#	else:
							#		continue
						else:
							hyp_stand = "standard"
						"""
						number_of_files = len(file_list)

						try:
							with open(file, 'rb') as f:
								histogram = pickle.load(f)
							n += 1

						except KeyError:
							print("File {} not found".format(file))
						except:
							print("Error at file {}".format(file))

						########## merge histograms ##########

						# get all histogram values and store them in array
						data = np.transpose([histogram[cam][gain][0] for cam in histogram.keys()
											for gain in histogram[cam].keys()])

						# adaption for nicer plotting with matplotlib
						data = np.append(data, [data[np.shape(data)[0]-1]], axis=0)
						data = np.append([data[0]], data, axis=0)

						# get the column names to use for column names of DataFrame
						col = pd.MultiIndex.from_arrays(np.transpose([[key, key2] for key in histogram.keys()
											  for key2 in histogram[key].keys()]))

						# sum DF of all files
						try:
							charges = charges.add(pd.DataFrame(data, columns=col), fill_value=0)
						except (NameError, AttributeError):
							charges = pd.DataFrame(data, columns=col)

						try:
							# check if binning already exists in DF
							charges["bins"]
						except KeyError:
							# get binning of very first entry. The binning for all histograms
							# should be set the same when processing. Therefore only one binning
							# is stored in the dataframe
							binning = np.transpose(
								histogram[list(histogram.keys())[0]][
								list(histogram[list(histogram.keys())[0]].keys())[0]][1]
								)
							# adaption for nicer plotting with matplotlib
							binning = np.append(binning, binning[-1])

							charges["bins"] = binning

					#if cleaner in ['NullWaveformCleaner']:
					#	charge_dist[dtype][integrator, cleaner] = charges
					charge_dist[dtype][integrator, cleaner] = charges

					check_read_files(number_of_files, n)

					limits = [-1. , 4.]
					bins = 40

					output_directory = "{}/{}/charge_distributions/{}/{}/".format(odir, dtype, integrator, cleaner)
					# generate output directory
					os.system("mkdir -p {}".format(output_directory))
					plot_charge_distributions(charges, limits, integrator, cleaner, "{}".format(output_directory))


	if (charge_distributions):
		for dtype in charge_dist.keys():
			
			charge_dist_methods = charge_dist[dtype]


			compare_directory = "{}/{}/charge_distributions/all_methods/ED_compare/".format(odir, dtype)
			output_directory = "{}/{}/charge_distributions/all_methods/".format(odir, dtype)
			# generate output directory
			os.system("mkdir -p {}".format(output_directory))

			#os.system("mkdir -p {}".format(compare_directory))
			# charge distribution for data type

			compare_all_methods(charge_dist_methods, limits, output_directory,
				compare_directory, hyp_stand)


