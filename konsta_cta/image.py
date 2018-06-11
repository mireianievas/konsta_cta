import warnings
import numpy as np
from tables import *

# Calibration
#############
from ctapipe.calib.camera import CameraCalibrator

# Image Cleaning
################
from ctapipe.image.cleaning import tailcuts_clean

# Parametrization
#################
from ctapipe.image import hillas_parameters

from traitlets.config import Config
import sys

class ImagePreparer():
	''' Class to convert Hessio raw data from r0 data level
		to calibrated and cleaned images. Image cleaning
		performed using tailcut cleaning.
	
	'''

	# for storing data
	clean_images = {}
	hillas_moments = {}
	sum_images = {}
	sum_clean_images = {}
	mc_image = {}
	mc_energy = {}

	# number images
	energy2 = []
	core_x2 = []
	core_y2 = []
	n_clean_images = []
	n_images = []
	images_cams = {}
	clean_images_cams = {}

	# hillas
	number_pixels = []
	energy = []
	size = []
	length = []
	width = []
	skewness = []
	camera = []
	core_x = []
	core_y = []


	# from Tino
	pe_thresh = {
		"ASTRICam": 14,
		"LSTCam": 100,
		"NectarCam": 190}

	# for analysing HESSIO file
	r1 = "HESSIOR1Calibrator"

	trace_width = {
	    "ASTRICam": (10, 5),
	    "FlashCam": (4, 2),
	    "LSTCam": (4, 2),
	    "NectarCam": (6, 3),
	    "DigiCam": (4, 2),
	    "CHEC": (8, 4),
	    "SCTCam": (6, 3)}

	def __init__(self, integrator=None, cleaner=None, h5file=None):
		self.keys = None
		self.integrator = integrator
		self.cleaner = cleaner
		self.h5file = h5file
	
		# From Tino: https://github.com/tino-michael/tino_cta/blob/master/tino_cta/ImageCleaning.py
		self.tail_thresholds = {"ASTRICam": (5, 7),  # (5, 10)?
					 "FlashCam": (12, 15),
					 "LSTCam": (5, 10),  # ?? (3, 6) for Abelardo...
					 # ASWG Zeuthen talk by Abelardo Moralejo:
					 "NectarCam": (4, 8),
					 # "FlashCam": (4, 8),  # there is some scaling missing?
					 "DigiCam": (3, 6),
					 "CHEC": (2, 4),
					 "SCTCam": (1.5, 3)}


	def prepare(self, particles, hillas=True, subarray=np.arange(600)):
		''' Performs the processing of the images:
			calibration perfoming conversion from r0 to dl1
			image cleaning using tailcut_cleaning
			image parametrization with Hillas parameters
			
			Fills the dicts for clean_images and hillas moments
		'''
		# Input
		#######
		# particles - array of konsta_cta.readdata.FileReader
		#

		self.particles = particles
		self.geoms, self.geoms_unique = self.get_camera_geoms()

		# loop through all particle types
		for particle in self.particles:
			dtype = particle.datatype

			# count number of images and number after cleaning
			self.sum_images[dtype] = 0
			self.sum_clean_images[dtype] = 0
			
			# dict to store the hisograms
			self.histograms = {}
			# loop through all events
			for event in particle.source:
				
				event_id = event.dl0.event_id
				n_images = 0
				n_clean_images = 0

				# count for each camera individually
				images_cams = {}
				clean_images_cams = {}

				self.mc_energy[dtype, event_id] = event.mc.energy
				# loop through all telescopes with data
				for tel_id in event.r0.tels_with_data:
					if type(subarray[0]) != str:
						subarray = [str(x) for x in subarray]

					if str(tel_id) in subarray:
						pass
					else:
						continue

					n_images += 1
					# get camera information
					camera = event.inst.subarray.tel[tel_id].camera

					try:
						# check if key already exists. if not initialize it with value 0
						_im = images_cams[camera.cam_id]
						_im = clean_images_cams[camera.cam_id]
					except KeyError:
						images_cams[camera.cam_id] = 0
						clean_images_cams[camera.cam_id] = 0

					# count for each camera individually
					images_cams[camera.cam_id] += 1


					cfg = Config()
					cfg["ChargeExtractorFactory"]["product"] = self.integrator
					cfg["ChargeExtractorFactory"]["window_width"] = self.trace_width[camera.cam_id][0]
					cfg["ChargeExtractorFactory"]["window_shift"] = self.trace_width[camera.cam_id][1]
					cfg['WaveformCleanerFactory']['product'] = self.cleaner

					# usually all cameras are calibrated at once with the same camera.
					# In order to force a racalculation to use the differen width and 
					# shift of the camera of this telescope, dl1 container will be reset
					# to default at each iteration.
					#
					#Probably it is not even needed to reset this, as the container
					#is refilled anyway.
					event.dl1.tel[tel_id].reset()
					# danger: The resulting calibrated event doesn't contain the right
					# extracted charges for all cameras in the end as it seems like
					# the dl1 images are overwirtten each time so that, the charges,
					# extracted at the last telescope iteration will be contained in the
					# dl1 container.
					# As I'm wirting out all the required information for the telescope
					# within this loop, this should not be much of a problem for now, but
					# in the future a appropriate way to work arround this is required.

					# set up calibrator.
					calibrator = CameraCalibrator(r1_product=self.r1, config=cfg)

					# calibrate event
					calibrator.calibrate(event)

					######################################
					# create output for comparison plots #
					######################################

					cam_id = camera.cam_id
					number_gains = event.dl1.tel[tel_id].image.shape[0]

					# create dict for the camera on first appearance
					try:
						_hist = self.histograms[cam_id]
					except KeyError:
						self.histograms[cam_id] = {}

					# fill histograms and merge for all events dependent on gain
					

					for gain, label in zip(range(number_gains), ["gain1", "gain2"]):
						image = np.array(event.dl1.tel[tel_id].image[gain])
						# only positive charges
						
						hist_lower = len(image[image > np.power(10.,-1.)])
						hist_higher = len(image[image > np.power(10.,4.)])

						image = image[image > 0]
						logimage = np.log10(image)
						hist = np.histogram(logimage, range=[-1,4], bins=100)

						# store the values outside of range for sanity check
						_hist = np.append(hist_lower, hist[0])
						_hist = np.append(_hist, hist_higher)
						_bins = np.append(-1000, hist[1])
						_bins = np.append(_bins, 1000)
						hist = (_hist, _bins)

						try:
							self.histograms[cam_id][label] = (self.histograms[cam_id][label][0] + hist[0],
														   self.histograms[cam_id][label][1])
						except KeyError:
							self.histograms[cam_id][label] = hist


					#####################################
					# Tino's solution for gain selection
					if (camera.cam_id == np.array(list(self.pe_thresh.keys()))).any():
						image = event.dl1.tel[tel_id].image
						image = self.pick_gain_channel(image, camera.cam_id)
					else:
						image = event.dl1.tel[tel_id].image
						image = np.reshape(image[0], np.shape(image)[1])

					######################
					# image cleaning
					# Threshold values adapted from Tino's repository
					mask = tailcuts_clean(
						self.geoms[tel_id], image,
						picture_thresh=self.tail_thresholds[camera.cam_id][1],
						boundary_thresh=self.tail_thresholds[camera.cam_id][0],
						min_number_picture_neighbors=0)

					try:
						temp_list
					except NameError:
						temp_list = []

					if not (camera.cam_id in temp_list):
						temp_list.append(camera.cam_id)
						print("Threshold {camera}: {threshold}".format(
							camera=camera.cam_id ,threshold=self.tail_thresholds[camera.cam_id]))

					number_pixels = np.count_nonzero(mask)

					# drop images that didn't survive image cleaning
					if any(mask == True):
						n_clean_images += 1
						self.clean_images[dtype, event_id, tel_id] = np.copy(image)
						# set rejected pixels to zero
						self.clean_images[dtype, event_id, tel_id][~mask] = 0

						# count for each camera individually
						try:
							clean_images_cams[camera.cam_id] += 1
						except KeyError:
							clean_images_cams[camera.cam_id] = 1

					### hillas parametrization
						if hillas:
							hillas_moments = hillas_parameters(
								self.geoms[tel_id], self.clean_images[dtype, event_id, tel_id], True)
							
							self.number_pixels.append(number_pixels) 
							self.energy.append(event.mc.energy.base)
							self.size.append(hillas_moments.intensity)
							self.length.append(hillas_moments.length)
							self.width.append(hillas_moments.width)
							self.skewness.append(hillas_moments.skewness)
							self.camera.append(camera.cam_id)
							self.core_x.append(event.mc.core_x.base)
							self.core_y.append(event.mc.core_y.base)
						else:
							pass



				# count number of images at trigge level and after cleaning
				# summary:
				self.sum_images[dtype] += n_images
				self.sum_clean_images[dtype] += n_clean_images
				# per event:
				self.core_x2.append(event.mc.core_x.base)
				self.core_y2.append(event.mc.core_y.base)
				self.energy2.append(event.mc.energy.base)
				self.n_images.append(float(n_images))
				self.n_clean_images.append(float(n_clean_images))

				for cam in images_cams.keys():
					try:
						self.images_cams[cam].append(float(images_cams[cam]))
						self.clean_images_cams[cam].append(float(clean_images_cams[cam]))
					except:
						self.images_cams[cam] = [float(images_cams[cam])]
						self.clean_images_cams[cam] = [float(clean_images_cams[cam])]


			print("Processed {} images for datatype {}. Images " 
				   "that didn't survive cleaning: {}".format(
					self.sum_images[dtype], dtype,
					self.sum_images[dtype] - self.sum_clean_images[dtype])
				  )

		self.get_keys()


	def get_keys(self):
		# returns numpy array of the keys
		self.keys = np.array(list(self.clean_images.keys()))
		#self.keys2 = np.array(list(self.n_clean_images.keys()))

	def get_camera_geoms(self):
		# returns dict of all camera geometries
		geoms = None
		for particle in self.particles:
			# get the first event:
			for event in particle.source:
				break

			# read the camera imformations for al telescopes
			_geoms = {}
			for tel_id in event.inst.subarray.tel_id.item():
				_geoms[tel_id] = event.inst.subarray.tel[tel_id].camera

			# Check geometry for all particle files 
			if not geoms:
				geoms = _geoms
			else:
				if geoms == _geoms:
					pass
				else:
					warnings.warn('Not same camera geometries for the files'
						'occured for: {}'.format(particle.datatype))

			geoms_unique = []
			for geo in geoms:
				try:
					if not any(geoms[geo].cam_id == np.array(geoms_unique)):
						geoms_unique.append(geoms[geo].cam_id)
				except:
					if len(geoms_unique)==0:
						geoms_unique.append(geoms[geo].cam_id)
					
		return(geoms, geoms_unique)

	def pick_gain_channel(self, pmt_signal, cam_id):
		'''the PMTs on some (most?) cameras have 2 gain channels. select one
		according to a threshold. ultimately, this will be done IN the
		camera/telescope itself but until then, do it here
		'''
		np_true_false = np.array([[True], [False]])
		if pmt_signal.shape[0] > 1:
			pmt_signal = np.squeeze(pmt_signal)
			pick = (self.pe_thresh[cam_id] <
					pmt_signal).any(axis=0) != np_true_false
			pmt_signal = pmt_signal.T[pick.T]
		else:
			pmt_signal = np.squeeze(pmt_signal)
		return pmt_signal

