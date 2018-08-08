import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
"""
def change_binning(hist ,bins, limits):
	'''
	Input
	-----
	histogram - tuple containing bin content and bins
	bins 	  - number of bins after the change
	limit 	  - which range to consider

	Note that this method should work best with high number of bins
	in the original histogram. Furthermore not to run into edge effects
	the range for the new histogram should be smaller and right in the
	middle of the original histogram's range.
	'''
	binning = hist[1]
	bins = bins + 1
	
	relevant_bins = np.arange(len(binning))[(binning > limits[0]) & (binning < limits[1] + np.diff(limits)/bins )]

	missing_bins = bins - np.mod(len(relevant_bins), bins)

	for i in range(missing_bins):
		if min(relevant_bins) > 0:
			k = (-1)**i
		else:
			k = 1

		if k == 1:
			relevant_bins = np.append(relevant_bins, max(relevant_bins) + 1)
		if k == -1:
			relevant_bins = np.append(min(relevant_bins) - 1, relevant_bins)
	step = len(relevant_bins)/bins
	
	binstep = relevant_bins[np.arange(0, len(relevant_bins), step, dtype=int)]
	
	histogram = []
	for i in range(len(binstep)-1):
		try:
			histogram = np.append(histogram, np.sum(hist[0][binstep[i]:binstep[i+1]]))
		except NameError:
			histogram = np.array([np.sum(hist[0][binstep[i]:binstep[i+1]])])

	bins = hist[1][binstep]
	
	histogram = np.append([0],histogram)
	histogram = np.append(histogram,[0])
	bins = np.append(bins, bins[-1])
	
	histogram[histogram<=0] = 10e-10

	return histogram, bins

def change_binning_simple(hist, sum_bins=10):
	for i in range(int(len(hist[0])/sum_bins)):
		start = i * sum_bins
		stop = (i+1)*sum_bins
		
		try:
			entry = np.sum(hist[0][start:stop])
			histogram = np.append(histogram, entry)
			bins = np.append(bins, hist[1][i*sum_bins])
		except:
			histogram = np.array([np.sum(hist[0][(i*sum_bins):((i+1)*sum_bins)])])
			bins = np.array(hist[1][i*sum_bins])

	#histogram[histogram<=0] == 1e-5
	return histogram, bins
"""



def plot_charge_distributions(charges, limits, integrator, cleaner, save=None, compare=None, hyp_stand = "hyper"):

	linewidth = 2
	alpha = 0.75

	bins = charges["bins"]

	# all cameras
	for cam in charges.keys().levels[0][charges.keys().levels[0]!="bins"]:
		fig = plt.figure(figsize=[10,6])
		ax = fig.add_subplot(111)
		for gain in charges[cam].keys():
			ax.plot(bins, np.log10(charges[cam][gain]), ls="steps", label="{}, {}".format(cam, gain))
		#ax.set_ylim(ymin=0)
		ax.set_xlim(limits)
		ax.set_xlabel("log(charge) [phe]", fontsize=12)
		ax.set_ylabel("log(Number of pixels)", fontsize=12)
		plt.title("{}, {}, {}".format(cam, integrator, cleaner), fontsize=15)
		plt.legend()
		plt.tight_layout()
		plt.savefig(save+"charges_camera_{}.pdf".format(cam))
		plt.close()


	# all cameras and gain
	for cam in charges.keys().levels[0][charges.keys().levels[0]!="bins"]:
		fig = plt.figure(figsize=[10,6])
		ax = fig.add_subplot(111)
		for gain in charges[cam].keys():
			ax.plot(bins, np.log10(charges[cam][gain]), ls="steps", label="{}, {}".format(cam, gain))
	#ax.set_ylim(ymin=0)
	ax.set_xlim(limits)
	ax.set_xlabel("log(charge) [phe]", fontsize=12)
	ax.set_ylabel("log(Number of pixels)", fontsize=12)
	plt.title("{}, {}, {}".format(cam, integrator, cleaner), fontsize=15)
	plt.legend()
	plt.tight_layout()
	plt.savefig(save+"charges_camera_{}.pdf".format(cam))
	plt.close()

"""		
################# ########################
	# all gains for each camera
	for cam in charges.keys():
		fig = plt.figure(figsize=[10,6])
		ax = fig.add_subplot(111)
		for gain in charges[cam].keys():
			try:
				histogram, binning = change_binning_simple(charges[cam][gain], 10)
				plt.plot(binning, histogram, ls="steps", label="{}, {}".format(cam, gain))
			except:
				pass
		plt.ylim(0)
		plt.xlim(limits)
		plt.xlabel("log(charge) [phe]", fontsize=12)
		plt.ylabel("Number of pixels", fontsize=12)
		#plt.legend(fontsize=12)
		plt.title("{}, {}, {}".format(cam, integrator, cleaner), fontsize=15)
		plt.savefig(save+"charges_camera_{}.pdf".format(cam))
		plt.close()


	# all cameras and gain
	plt.figure(figsize=[10,6])
	for cam in charges.keys():

		for gain in charges[cam].keys():
			try:
				histogram, binning = change_binning_simple(charges[cam][gain], 10)
				plt.plot(binning, histogram, ls="steps", label="{}, {}".format(cam, gain))
			except:
				pass
	plt.ylim(0)
	plt.xlim(limits)
	plt.xlabel("log(charge) [phe]", fontsize=12)
	plt.ylabel("Number of pixels", fontsize=12)
	#plt.legend(fontsize=12)
	plt.title("{} {}".format(integrator, cleaner), fontsize=15)
	plt.savefig(save+"charges_all_cameras.pdf")
	plt.close()

"""


def compare_all_methods(charges, limits, save=None,  compare=None, hyp_stand = "hyper"):
	linewidth = 2

	# get all cameras
	for method in charges.keys():
		cams = charges[method].columns.levels[0]#[charges.keys().levels[0]!="bins"]
		cams = cams[cams!="bins"]
		break

	# loop through all cameras
	for cam in cams:
		fig = plt.figure(figsize=[10,6])
		ax = fig.add_subplot(111)
		for method in charges.keys():
			try:
				bins
			except NameError:
				bins = charges[method]["bins"]
			sum_hist = np.sum(charges[method][cam]["gain1"])
			ax.plot(bins, np.log10(charges[method][cam]["gain1"]), ls="steps", linewidth=linewidth,
				label="{} {}, gain1".format(method[0][:5], method[1][-6:]), alpha=0.8)
			if cam in ["ASTRICam", "LSTCam", "NectarCam"]:
				ax.plot(bins, np.log10(charges[method][cam]["gain2"]), ls="steps", linewidth=linewidth,
					label="{} {}, gain2".format(method[0][:5], method[1][-6:]), alpha=0.8)
		#ax.set_ylim(ymin=0)
		ax.set_xlim(limits)
		ax.set_xlabel("log(charge) [phe]", fontsize=12)
		ax.set_ylabel("log(Number of pixels)", fontsize=12)
		plt.title("Integrated charges {}".format(cam), fontsize=15)
		plt.legend()
		plt.tight_layout()
		plt.savefig(save+"charges_methods_{}.pdf".format(cam))
		plt.close()

	# loop through all cameras
	for cam in cams:
		if cam in ["FlashCam"]:
			fig = plt.figure(figsize=[10,6])
			ax = fig.add_subplot(111)
			for method in charges.keys():
				try:
					bins
				except NameError:
					bins = charges[method]["bins"]
				sum_hist = np.sum(charges[method][cam]["gain1"])
				ax.plot(bins, np.log10(charges[method][cam]["gain1"]/sum_hist), ls="steps", linewidth=linewidth,
					label="{} {}, gain1".format(method[0][:5], method[1][-6:]), alpha=0.6)
				if cam in ["ASTRICam", "LSTCam", "NectarCam"]:
					ax.plot(bins, np.log10(charges[method][cam]["gain2"]), ls="steps", linewidth=linewidth,
						label="{} {}, gain2".format(method[0][:5], method[1][-6:]), alpha=0.6)
			#ax.set_ylim(ymin=0)
			ax.set_xlim(limits)
			ax.set_xlabel("log(charge) [phe]", fontsize=12)
			ax.set_ylabel("log(Number of pixels)", fontsize=12)
			plt.title("Integrated charges {}".format(cam), fontsize=15)
			plt.legend()
			plt.tight_layout()
			#plt.savefig(save+"charges_methods_{}_normed.pdf".format(cam))
			plt.close()


	# gain2
	if hyp_stand=="hyper":
		cams_gain2 = ["ASTRICam", "LSTCam", "NectarCam"]
	elif hyp_stand=="standard":
		cams_gain2 = ["LSTCam"]

	for cam in cams_gain2:
		fig = plt.figure(figsize=[10,6])
		ax = fig.add_subplot(111)
		for method in charges.keys():
			try:
				bins
			except NameError:
				bins = charges[method]["bins"]
			sum_hist = np.sum(charges[method][cam]["gain2"])
			if method[1]=="NullWaveformCleaner":
				ax.plot(bins, np.log10(charges[method][cam]["gain2"]), ls="steps", linewidth=linewidth,
					label="{}, {}, gain2".format(method[0][:5], method[1][-6:]), alpha=0.5, color="black")
			else:
				ax.plot(bins, np.log10(charges[method][cam]["gain2"]), ls="steps", linewidth=linewidth,
					label="{}, {}, gain2".format(method[0][:5], method[1][-6:]), alpha=0.8)
		#ax.set_ylim(ymin=0)
		ax.set_xlim(limits)
		ax.set_xlabel("log(charge) [phe]", fontsize=12)
		ax.set_ylabel("log(Number of pixels)", fontsize=12)
		plt.title("Integrated charges {}".format(cam), fontsize=15)
		plt.legend()
		plt.tight_layout()
		plt.savefig(save+"charges_methods__{}_lg.pdf".format(cam))
		plt.close()


	# gain1
	for cam in cams_gain2:
		fig = plt.figure(figsize=[10,6])
		ax = fig.add_subplot(111)
		for method in charges.keys():
			try:
				bins
			except NameError:
				bins = charges[method]["bins"]
			sum_hist = np.sum(charges[method][cam]["gain1"])
			
			ax.plot(bins, np.log10(charges[method][cam]["gain1"]), ls="steps", linewidth=linewidth,
				label="{}, {}, gain1".format(method[0][:5], method[1][-6:]), alpha=0.8)
		#ax.set_ylim(ymin=0)
		ax.set_xlim(limits)
		ax.set_xlabel("log(charge) [phe]", fontsize=12)
		ax.set_ylabel("log(Number of pixels)", fontsize=12)
		plt.title("Integrated charges {}".format(cam), fontsize=15)
		plt.legend()
		plt.tight_layout()
		plt.savefig(save+"charges_methods__{}_hg.pdf".format(cam))
		plt.close()

	# No waveformcleaning
	for cam in cams:
		fig = plt.figure(figsize=[10,6])
		ax = fig.add_subplot(111)
		for method in charges.keys():
			if method[1]=="NullWaveformCleaner":
				try:
					bins
				except NameError:
					bins = charges[method]["bins"]
				sum_hist = np.sum(charges[method][cam]["gain1"])
				ax.plot(bins, np.log10(charges[method][cam]["gain1"]), ls="steps", linewidth=linewidth,
					label="{}, gain1".format(method[0]), alpha=0.8)
				if cam in ["ASTRICam", "LSTCam", "NectarCam"]:
					ax.plot(bins, np.log10(charges[method][cam]["gain2"]), ls="steps", linewidth=linewidth,
						label="{}, gain2".format(method[0]), alpha=0.8)
		#ax.set_ylim(ymin=0)
		ax.set_xlim(limits)
		ax.set_xlabel("log(charge) [phe]", fontsize=12)
		ax.set_ylabel("log(Number of pixels)", fontsize=12)
		plt.title("Integrated charges {}".format(cam), fontsize=15)
		plt.legend()
		plt.tight_layout()
		plt.savefig(save+"charges_methods_{}.pdf".format(cam))
		plt.close()




####################################################################################
		####################################################################		
				####################################################													
						####################################		
								####################		
										####	


# This comparison is done only for a small number of events ==> do it in notbook?
























#######################################################################################
#######################################################################################
#######################################################################################




	###################
	"""	
	for integrator in charges.keys():
		for cleaner in charges[integrator].keys():
			cameras = charges[integrator][cleaner].keys()

	for cam in cameras:
		for gain in charges["GlobalPeakIntegrator"]["NullWaveformCleaner"][cam].keys():
			for integrator in ['GlobalPeakIntegrator', 'LocalPeakIntegrator',
							   'NeighbourPeakIntegrator', 'AverageWfPeakIntegrator']:
				for cleaner in ['NullWaveformCleaner', 'CHECMWaveformCleanerAverage',
								'CHECMWaveformCleanerLocal']:
					try:
						change_binning_simple(charges[cam][gain], 10)
						plt.plot(binning, charges, ls="steps", label="{}, {}".format(integrator[:5],cleaner[:5]))
					except:
						pass
			plt.ylim(0)
			plt.xlim(limits)
			plt.yscale('log')
			plt.xlabel("log(charge) [phe]", fontsize=12)
			plt.ylabel("Number of pixels", fontsize=12)
			plt.legend(fontsize=12)
			plt.title("{}".format(cam, gain), fontsize=17)
			plt.savefig(save+"charges_methods_{}_{}.pdf".format(cam, gain))
			plt.close()	
	"""
	###########################################################
	'''
	# all methods:
	methods = histograms.keys()
	for method in methods:
		
		# all runs:
		runs = histograms[method].keys()
		for run in runs:

			# all cameras and gains
			cameras_gains = histograms[method][run].keys()
		break
	'''
	'''
	the for all methods exactly the same runs and cameras
	are used. Therefor by using the keys for the first
	entry each gives a complete list of all possible cameras
	and runs.
	'''
	'''
	# merge all runs together
	hist = {}
	for method in methods:
		hist[method] = {}
		for camera_gain in cameras_gains:
			for run in runs:

				try:
					hist[method][camera_gain] = (
						hist[method][camera_gain][0] + histograms[method][run][camera_gain][0],
						hist[method][camera_gain][1]
						)
				except KeyError:
					hist[method][camera_gain] = histograms[method][run][camera_gain]

	##################### All gains for each camera ###########
	for method in methods:
		# name of cameras and multiplicity
		cameras, gains = np.unique(np.array(list(hist[method].keys()))[:,0], return_counts=True)
		# keys of camera_gain
		keys_cameras = np.array(list(hist[method].keys()))
		for camera in cameras:
			plt.figure(figsize=[10,6])

			# select keys for this camera type
			mask = keys_cameras[:,0] == camera
			keys = keys_cameras[mask]

			for key in keys:
				HISTO, bins = hist[method][key[0], key[1]]

				# To make histograms matplotlib hist like when plotting as step function
				HISTO = np.append([0],HISTO)
				HISTO = np.append(HISTO,[0])
				bins = np.append(bins, bins[-1])

				# Different gains in each camera
				plt.plot(bins, HIST0, ls="step", label="{}, gain {}".format(camera_gain))
			plt.ylim(0)
			plt.xlim(limits)
			plt.xlabel("log(charge) [phe]", fontsize=12)
			plt.ylabel("Number of pixels", fontsize=12)
			plt.legend(fontsize=12)
			plt.title("{}".format(camera), fontsize=17)
			plt.savefig(save+"{}/{}/charges_{}.pdf".format(method[0], method[1], camera))
			plt.close()


	################### All cameras and gains ####################
	for method in methods:
		for camera_gain in cameras_gains:
			
			HISTO, bins = hist[method][camera_gain]
			
			# To make histograms matplotlib hist like when plotting as step function
			HISTO = np.append([0],HISTO)
			HISTO = np.append(HISTO,[0])
			bins = np.append(bins, bins[-1])
			plt.figure(figsize=[10,6])
			plt.plot(bins, HIST0, ls="step", label="{} gain{}".format(camera_gain[0], camera_gain[1]))
		plt.ylim(0)
		plt.xlim(limits)
		plt.xlabel("log(charge) [phe]", fontsize=12)
		plt.ylabel("Number of pixels", fontsize=12)
		plt.legend(fontsize=12)
		plt.title("All telescopes", fontsize=17)
		plt.savefig(save+"{}/{}/charges_all_tels.pdf".format(method[0], method[1]))


	################ All methods for each camera and gain ##############
	for camera_gain in cameras_gains:
		for method in methods:

			HISTO, bins = hist[method][camera_gain]
			
			# To make histograms matplotlib hist like when plotting as step function
			HISTO = np.append([0],HISTO)
			HISTO = np.append(HISTO,[0])
			bins = np.append(bins, bins[-1])				

			plt.figure(figsize=[10,6])
			plt.plot(bins, HIST0, ls="step", label="{}, gain {}".format(camera_gain))
		plt.ylim(0)
		plt.xlim(limits)
		plt.xlabel("log(charge) [phe]", fontsize=12)
		plt.ylabel("Number of pixels", fontsize=12)
		plt.legend(fontsize=12)
		plt.title("All telescopes", fontsize=17)
		plt.savefig(save+"charges_{}_{}.pdf".format(camera_gain[0], camera_gain[1]))

	'''

"""
			# All Telescopes and gains
			plt.figure(figsize=[10,6])
			for key in phe_charge:
				charges = phe_charge[key]
				charges = np.array(charges)
				# only positive values
				mask = (charges > 0)
				phe = np.log10(charges[mask])
				# cut events outside of limits
				mask2 = (phe > limits[0]) & (phe < limits[1])
				phe = phe[mask2]

				plt.hist(phe, bins=bins, histtype='step', label="{}, {}".format(key[0],key[1]),
						 log=True, linewidth=linewidth, alpha=alpha)
			plt.xlabel("log(charge) [phe]", fontsize=12)
			plt.ylabel("Number of pixels", fontsize=12)
			plt.xlim(limits)
			plt.legend(fontsize=12)
			plt.title("All telescopes", fontsize=17)
			splt.tight_layout()
			plt.savefig(save+"{}/{}/charges_all_Tels.pdf".format(integrator[:5], cleaner[:5]))


			# Seperated for each telescope with different gains
			cameras, gains = np.unique(np.array(list(phe_charge.keys()))[:,0], return_counts=True)
			all_keys = np.array(list(phe_charge.keys()))

			for camera in cameras:
				plt.figure(figsize=[10,6])
				# all gain channels for this camera type
				mask = all_keys[:,0] == camera
				keys = all_keys[mask]
				
				for key in keys:
					charges = phe_charge[key[0], int(key[1])]
					charges = np.array(charges)
					# only positive values
					mask = (charges > 0)
					phe = np.log10(charges[mask])
					# cut events outside of limits
					mask2 = (phe > limits[0]) & (phe < limits[1])
					phe = phe[mask2]

					plt.hist(phe, bins=bins, histtype='step', label="gain {}".format(key[1]),
							 log=True, alpha=alpha, linewidth=linewidth)
				plt.xlabel("log(charge) [phe]", fontsize=12)
				plt.ylabel("Number of pixels", fontsize=12)
				plt.xlim(limits)
				plt.legend(fontsize=12)
				plt.title(key[0], fontsize=17)
				plt.tight_layout()
				plt.savefig(save+"{}/{}/charges_{}.pdf".format(integrator[:5], cleaner[:5], key[0]))
			

	# comparison of all methods for each telescope and gain
	for key in all_keys:
		for integrator in ['GlobalPeakIntegrator', 'LocalPeakIntegrator',
					   'NeighbourPeakIntegrator', 'AverageWfPeakIntegrator']:
			for cleaner in ['NullWaveformCleaner', 'CHECMWaveformCleanerAverage',
							'CHECMWaveformCleanerLocal']:
				# get one methode
				phe_charge = phe_charge_all[integrator, cleaner]
				# entries for telescope and gain
				charges = phe_charge[key]
				charges = np.array(charges)
				# only positive values
				mask = (charges > 0)
				phe = np.log10(charges[mask])
				# cut events outside of limits
				mask2 = (phe > limits[0]) & (phe < limits[1])
				phe = phe[mask2]

				# plot restults for all integrators and cleaners in one plot
				plt.hist(phe, bins=bins, histtype='step', label="{}, {}".format(integrator[:5],
						cleaner[3]), log=True, linewidth=linewidth, alpha=alpha)
				plt.xlabel("log(charge) [phe]", fontsize=12)
		plt.ylabel("Number of pixels", fontsize=12)
		plt.xlim(limits)
		plt.legend(fontsize=12)
		plt.title("{}, different methods".format(key[0]), fontsize=17)
		plt.tight_layout()
		plt.savefig(save+"{}_gain{}_charges_comparison_methods.pdf".format(key[0], key[1]))
"""