from ctapipe.io import event_source	# file reader

# perpare a event
from prepare_featurelist import PrepareList, MultiplicityException
from direction_LUT import *
from ctapipe.reco.HillasReconstructor import TooFewTelescopesException

# read configurations
import json 
import argparse
#import sys

# saving of output
import tables as tb 
import pickle

# general data processing
import numpy as np
import pandas as pd
from astropy import units as u
from astropy.coordinates.angle_utilities import angular_separation
from datetime import datetime

import os
import warnings
# some conflicts with numpy in HillasReconstructor (?)
# it should not spam the output:
warnings.simplefilter(action='ignore', category=FutureWarning)
# mouting RuntimeWarning for np.sqrt calculation
warnings.simplefilter(action='ignore', category=RuntimeWarning)


class ReconstructionWarning(UserWarning):
	pass


class EventFeatures(tb.IsDescription):
	impact = tb.Float32Col(dflt=1, pos=0)
	sum_signal_event = tb.Float32Col(dflt=1, pos=1)
	max_signal_camera = tb.Float32Col(dflt=1, pos=2)
	sum_signal_camera = tb.Float32Col(dflt=1, pos=3)
	N_LST = tb.Int16Col(dflt=1, pos=4)
	N_MST = tb.Int16Col(dflt=1, pos=5)
	N_SST = tb.Int16Col(dflt=1, pos=6)
	width = tb.Float32Col(dflt=1, pos=7)
	length = tb.Float32Col(dflt=1, pos=8)
	skewness = tb.Float32Col(dflt=1, pos=9)
	kurtosis = tb.Float32Col(dflt=1, pos=10)
	h_max = tb.Float32Col(dflt=1, pos=11)
	err_est_pos = tb.Float32Col(dflt=1, pos=12)
	MC_Energy = tb.FloatCol(dflt=1, pos=13)
	Primary_ID = tb.Int16Col(dflt=1, pos=14)

class DCAFeatures(tb.IsDescription):
	intensity = tb.Float32Col(dflt=1, pos=1)
	width = tb.Float32Col(dflt=1, pos=2)
	length = tb.Float32Col(dflt=1, pos=3)
	skewness = tb.Float32Col(dflt=1, pos=4)
	kurtosis = tb.Float32Col(dflt=1, pos=5)
	r = tb.Float32Col(dflt=1, pos=6)
	DCA = tb.Int16Col(dflt=1, pos=7)

class DirectionReconstruction(tb.IsDescription):
	Primary_ID = tb.Int16Col(dflt=1, pos=1)
	MC_Energy = tb.FloatCol(dflt=1, pos=2)
	MC_az = tb.FloatCol(dflt=1, pos=3)
	MC_alt = tb.FloatCol(dflt=1, pos=4)
	REC_az = tb.FloatCol(dflt=1, pos=5)
	REC_alt = tb.FloatCol(dflt=1, pos=6)
	off_angle = tb.FloatCol(dflt=1, pos=7)


if __name__ == '__main__':
	start = datetime.now()

	parser = argparse.ArgumentParser()
	parser.add_argument("--filepath", type=str, default=None,
						help="file to process")
	parser.add_argument("--outputfile", type=str, default=".",
						help="output directory")
	parser.add_argument("--tels_to_use", type=str, default="all",
						help="telescopes to use")
	parser.add_argument("--config", type=str, default="config.json",
						help="configuration file")
	parser.add_argument("--ctapipe_aux_dir", type=str, default="",
						help="directory with additional files (LUT)")
	args = parser.parse_args()

	file = args.filepath
	outputfile = args.outputfile
	tels_to_use = args.tels_to_use
	ctapipe_aux_dir = args.ctapipe_aux_dir

	#read config
	with open(args.config) as json_file:
			config = json.load(json_file)

	print("\nConfigurations used for this ananlysis:\n")
	print(config)
	print("---------------------------------------")


	# read the simtel file
	source = event_source(file, max_events=None)
	
	#try:
	#	# read the simtel file
	#	source = event_source(file, max_events=None)
	#except FileNotFoundError:
	#	print("File {} not found.".format(file))
	#	sys.exit("exiting...")

	event = next(iter(source)) # get one event to extract some informations

	if tels_to_use != "all":
		# read list of telescopes to use for analysis
		with open("{}".format(tels_to_use)) as f:
			telescope_list = f.read().splitlines()
			telescope_list = np.array(telescope_list, dtype=int)
	else:
		# hyperarray
		telescope_list = np.arange(1, event.inst.subarray.num_tels+1)

	print("Telescopes to use: \n{}".format(telescope_list))


	# get list with all cameras to analyze
	camera_types = []
	for tel_id in telescope_list:
		cam_id = event.inst.subarray.tel[tel_id].camera.cam_id
		if not cam_id in camera_types:
			camera_types.append(cam_id)

	LUTgenerator = None
	if config["mode"] == "write_lists":
		outfile = tb.open_file("{}.h5".format(outputfile), mode="w")

		feature_table = {}
		feature_events = {}

		for cam_id in camera_types:
			# structure of the output file for feature list
			feature_table[cam_id] = outfile.create_table(
				'/', '_'.join(["feature_events", cam_id]), EventFeatures)
			feature_events[cam_id] = feature_table[cam_id].row

		# direction reconstruction
		direction_table = outfile.create_table(
			'/', "direction_reconstriction", DirectionReconstruction)
		direction_events = direction_table.row

		# determine which weighting to use during the 
		weight_methods = ["LUT", "default"]
		if config["Preparer"]["DirReco"]["weights"] == "LUT":
			LUTfile = "{}/{}".format(ctapipe_aux_dir, config["Preparer"]["DirReco"]["LUT"])

			LUTgenerator = LookupGenerator.load(LUTfile)

		elif config["Preparer"]["DirReco"]["weights"] == "default":
			pass
		else:
			raise KeyError("Method {} for weights in direction reconstruction"
						   " not known. Possible methods are {}".format(
						   config["Preparer"]["DirReco"]["weights"], weight_methods))

	elif config["mode"] == "write_list_dca":
		LUTgenerator = LookupGenerator() # for using the methods

		outfile = tb.open_file("{}.h5".format(outputfile), mode="w")

		dca_table = {}
		dca_events = {}
		for cam_id in camera_types:
			# structure of the output file for dca feature list
			dca_table[cam_id] = outfile.create_table(
				'/', '_'.join(["dca_events", cam_id]), DCAFeatures)
			dca_events[cam_id] = dca_table[cam_id].row


	elif config["mode"] == "make_direction_LUT":
		# make direction LUT
		LUTgenerator = LookupGenerator()

	# start main loop
	#################
	for event in source:

		# raw image to direction reconstructed
		eventpreparer = PrepareList(event, telescope_list, camera_types,
									**config["Preparer"], LUT=LUTgenerator)

		# get the parameters of the parametrization and reconstruction
		try:
			impact, max_signal, tot_signal, n_tels_types, hillas_moments, \
			reconstructed = eventpreparer.get_reconstructed_parameters()
		except (TooFewTelescopesException, MultiplicityException):
			continue

		# angular difference
		off_angle = angular_separation(event.mc.az, event.mc.alt, 
								reconstructed.az, reconstructed.alt)
		off_angle = off_angle.to(u.deg).value

		# number of telescopes
		n_tels = {"LST": 0, "MST": 0, "SST": 0}
		for tel in n_tels_types:
			if tel in "LSTCam":
				n_tels["LST"] += n_tels_types[tel]
			elif tel in ["NectarCam", "FlashCam"]:
				n_tels["MST"] += n_tels_types[tel]
			elif tel in ["CHEC", "ASTRICam", "DigiCam"]:
				n_tels["SST"] += n_tels_types[tel]

		if config["mode"] == "write_lists":
			# write parameters relevant for training energy regressors and
			# classifier of primary particles.
			try:
				for tel_id in hillas_moments.keys():
					cam_id = event.inst.subarray.tel[tel_id].camera.cam_id

					# feature list
					feature_events[cam_id]["impact"] = impact[tel_id] / u.m
					feature_events[cam_id]["sum_signal_event"] = tot_signal
					feature_events[cam_id]["max_signal_camera"] = max_signal[tel_id]
					feature_events[cam_id]["sum_signal_camera"] = hillas_moments[tel_id].intensity
					feature_events[cam_id]["N_LST"] = n_tels["LST"]
					feature_events[cam_id]["N_MST"] = n_tels["MST"]
					feature_events[cam_id]["N_SST"] = n_tels["SST"]
					feature_events[cam_id]["width"] = hillas_moments[tel_id].width / u.m
					feature_events[cam_id]["length"] = hillas_moments[tel_id].length / u.m
					feature_events[cam_id]["skewness"] = hillas_moments[tel_id].skewness
					feature_events[cam_id]["kurtosis"] = hillas_moments[tel_id].kurtosis
					feature_events[cam_id]["h_max"] = reconstructed.h_max / u.m
					feature_events[cam_id]["err_est_pos"] = reconstructed.core_uncert / u.m
					feature_events[cam_id]["MC_Energy"] = event.mc.energy / u.TeV
					feature_events[cam_id]["Primary_ID"] = event.mc.shower_primary_id
					feature_events[cam_id].append()

				# direction reconstruction results
				direction_events["Primary_ID"] = event.mc.shower_primary_id
				direction_events["MC_Energy"]  = event.mc.energy / u.TeV
				direction_events["MC_az"] = event.mc.az / u.deg
				direction_events["MC_alt"] = event.mc.alt / u.deg
				direction_events["REC_az"] = reconstructed.az / u.deg
				direction_events["REC_alt"] = reconstructed.alt / u.deg
				direction_events["off_angle"] = off_angle
				direction_events.append()

				outfile.flush()

			except TypeError:
				# happens if value of core reconstruction is without
				# astropy unit. Is it a bug in HillasReconstructor ?
				warnings.warn("Rconstruciton not succesfull for event {}"
							  .format(event.r0.event_id), ReconstructionWarning)
				continue


		if config["mode"] == "write_list_dca":
			# write parameters relevant for training energy regressors and
			# classifier of primary particles.
			try:
				for tel_id in hillas_moments.keys():
					cam_id = event.inst.subarray.tel[tel_id].camera.cam_id

					# get dca value
					direction_az = event.mc.az.to(u.deg)
					direction_alt = event.mc.alt.to(u.deg)
					cam_coord = LUTgenerator.get_position_in_cam(direction_alt,
														 direction_az, event, tel_id)
					dca = LUTgenerator.calculate_dca((cam_coord.x, cam_coord.y),
											 hillas_moments[tel_id])

					# for training of dca RF 
					dca_events[cam_id]["intensity"] = hillas_moments[tel_id].intensity
					dca_events[cam_id]["width"] = hillas_moments[tel_id].width / u.m
					dca_events[cam_id]["length"] = hillas_moments[tel_id].length / u.m
					dca_events[cam_id]["skewness"] = hillas_moments[tel_id].skewness
					dca_events[cam_id]["kurtosis"] = hillas_moments[tel_id].kurtosis
					dca_events[cam_id]["r"] = hillas_moments[tel_id].r
					dca_events[cam_id]["DCA"] = dca
					dca_events[cam_id].append()

					outfile.flush()

			except TypeError:
				# happens if value of core reconstruction is without
				# astropy unit. Is it a bug in HillasReconstructor ?
				warnings.warn("Rconstruciton not succesfull for event {}"
							  .format(event.r0.event_id), ReconstructionWarning)
				continue


		elif config["mode"] == "make_direction_LUT":
			# make a LUT for weights in direction reconstruction
			LUTgenerator.collect_data(event, hillas_moments)

	if config["mode"] == "make_direction_LUT":
		lookup = LUTgenerator.make_lookup(config["make_direction_LUT"]["size_max"],
								 bins=config["make_direction_LUT"]["bins"])
		LUTgenerator.save("{}.json".format(outputfile))

	elif config["mode"] in ["write_lists", "write_list_dca"]:
		outfile.close() # close remaining file

	stop = datetime.now()
	duration = stop - start
	print("##################################")
	print(" Succefully analyzed {} events ".format(event.count))
	print(" Duration: {}".format(duration))
	print("##################################\n")
	print("Output written to {} \n".format(outputfile))
	print("Reading the output:\n \
Feature tables:\n\
for cam_id in {cams}:\n\
	pandas.read_hdf('{file}', 'feature_events_{}'.format(cam_id))\n\n\
DCA feature table:\n\
for cam_id in {cams}:\n\
	pandas.read_hdf('{file}', 'dca_events_{}'.format(cam_id))\n\n\
Direction results:\n\
pandas.read_hdf({file}, key='direction_reconstriction')\
".format(cams=camera_types, file=outputfile))
