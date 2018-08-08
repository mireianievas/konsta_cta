import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import pandas as pd
import os

def MtoDEG(df):
	focal_length_tels = {
	"LSTCam": 28.,
	"FlashCam": 16,
	"NectarCam": 16,
	"ASTRICam": 2.15,
	"DigiCam": 5.6,
	"CHEC": 2.283,
	}
	df["mtodeg"] = -100
	for cam in np.unique(df["camera"]):
		conversion = (180 / (np.pi * focal_length_tels[cam]))
		df.loc[df.camera==cam, "mtodeg"] = conversion

	return df


def pixel_cut(df):
	for cam in ["LSTCam", "FlashCam", "NectarCam", "ASTRICam", "DigiCam", "CHEC"]:
		if (cam=="LSTCam") | (cam=="FlashCam") | (cam=="NectarCam"):
			pixelcut = 4
		elif (cam=="ASTRICam") | (cam=="DigiCam"):
			pixelcut = 5
		elif (cam=="CHEC"):
			pixelcut = 6

		df = df.drop(df[(df["camera"]==cam) & (df["number_pix"] <= pixelcut)].index)
	return df

def change_binning(histo, number_to_sum):
	histogram = np.array(histo.hists)
	hist_sum = None
	for k in range(number_to_sum):
		try:
			entries = len(histogram[k::number_to_sum])
			if entries == len(hist_sum):
				hist_sum = hist_sum + histogram[k::number_to_sum]
			else:
				hist_sum = hist_sum[:entries] + histogram[k::number_to_sum]
		except (NameError, TypeError):
			hist_sum = histogram[::number_to_sum]

	hist_sum = np.append(hist_sum[0], hist_sum)
	hist_sum = np.append(0, hist_sum)
	bins_ED =  np.append(histo.bins[0], histo.bins[::number_to_sum])

	return bins_ED, hist_sum

def change_binning_error(histo, number_to_sum):
<<<<<<< HEAD
	histo.hists[0] = 0
	histo.error[0] = 0
	histo.hists[1] = 0
	histo.error[1] = 0
=======
>>>>>>> 507fdcf53c4464f4822d763ecffe7109305ed0d6
	histogram = np.array(histo.hists)
	error = np.array(histo.error)
	hist_sum = None
	for k in range(number_to_sum):
		try:
			entries = len(histogram[k::number_to_sum])
			if entries == len(hist_sum):
				hist_sum = hist_sum + histogram[k::number_to_sum]
			else:
				hist_sum = hist_sum[:entries] + histogram[k::number_to_sum]
		except (NameError, TypeError):
			hist_sum = histogram[::number_to_sum]

	hist_sum = np.append(hist_sum[0], hist_sum)
	hist_sum = np.append(0, hist_sum)
	# sum errors
	err_sum = None
	for k in range(number_to_sum):
		try:
			entries = len(error[k::number_to_sum])
			if entries == len(err_sum):
				err_sum = err_sum + error[k::number_to_sum]
			else:
				err_sum = err_sum[:entries] + error[k::number_to_sum]
		except (NameError, TypeError):
			err_sum = error[::number_to_sum]
	err_sum = np.append(err_sum[0], err_sum)
	err_sum = np.append(0, err_sum)

	bins_ED =  np.append(histo.bins[0], histo.bins[::number_to_sum])

	return bins_ED, hist_sum, err_sum


def get_norm_factor(values):
    norm = np.sum(values) * ((len(values) -1) / len(values))
    return norm

def print_stat_error(bins, value, color=None, alpha=1, add=True, normed=False):
    '''
    input
    -----
    bins - position of bins
    value - values of unbinned histogram
    '''
    if add:
        value = np.append(value, value[-1])
    norm = get_norm_factor(value)
    error = np.sqrt(value)
    if normed:
        error = error / norm
        value = value / norm
    plt.fill_between(x=bins, y1=value+error, y2=value-error, edgecolor=None, step="post", alpha=alpha, color=color)



def plot_hillas(hillas, EventDisplay, MARS, tel_list, save=None, compare=None, hyp_stand="hyper", ED=True, witherr=False):

	# "Emc", "size", "length", "skewness", "camera", "width", "core_x", "core_y"
	

	#print(hillas.head(100))

	##### important: Bug in one_file (already fixed)!!
	# width --> Camera
	# skewness --> width
	# camera --> skewness
	#hillas["camera2"] = hillas["width"]
	#hillas["width"] = hillas["skewness"]
	#hillas["skewness"] = hillas["camera"]
	#hillas["camera"] = hillas["camera2"]



	# convert strings to floats
	for col in ["Emc", "size", "length", "skewness", "width", "core_x", "core_y", "number_pix"]:
		hillas[col] = pd.to_numeric(hillas[col], errors='coerce')

	hillas["core_dist"] = np.sqrt(hillas.core_x/100**2 + hillas.core_y/100**2)

	hillas["Emc_log"] = np.log10(hillas.Emc)
	hillas["core_log"] = np.log10(hillas.core_dist)


	# add conversion factor from ra to deg
	hillas = MtoDEG(hillas)
	MARS = MtoDEG(MARS)
	#remove ASTRI Cam
	hillas = hillas.drop(hillas[hillas["camera"]=="ASTRICam"].index)

	# apply number of pixel cut:
	#hillas_cutpix = pixel_cut(hillas)
	hillas_cutpix = hillas

	#range_size = np.log10([np.min(hillas["size"]), np.max(hillas["size"])])
	range_size = np.log10([np.min(hillas["size"]), np.max(hillas["size"])])
	range_pix_log = np.log10([np.min(hillas["number_pix"]), np.max(hillas["number_pix"])])
	range_pix = [np.min(hillas["number_pix"]), np.max(hillas["number_pix"])]

	range_width = [np.min(hillas["width"] * hillas["mtodeg"]), np.max(hillas["width"] * hillas["mtodeg"])]
	range_length = [np.min(hillas["length"] * hillas["mtodeg"]), np.max(hillas["length"] * hillas["mtodeg"])]
	range_lengthwidth = [np.min([range_width, range_length]), np.max([range_width, range_length])]

	cams = np.unique(hillas["camera"])

	# energy range between 10Gev and 100Tev
	ebins = np.linspace(-2, 2, 5)
	cbins = np.linspace(0, 2000, 5)


#######################################################################################
#######################################################################################
#######################################################################################

	  ########	  ###	   #########  ##########
	 ###		  ###	 	    ###   ###
	###			  ###		   ###	  ###
	 ###		  ###	 	  ###     ###
	  #######	  ###	     ###	  ##########
		   ###	  ###	    ###	      ###
			###   ###	   ###		  ###
		   ###	  ###	  ###	      ###
	 #######	  ###	 #########    ##########

	mean_size_energy = []
	std_size_energy = []
	mean_size_core = []
	std_size_core = []


	for binning, label in zip([ebins, cbins], ["Energy", "Core"]):
		fig = plt.figure(figsize=[7,6])
		for i in range(len(ebins) - 1):
			if label=="Energy":
				hillas_selected = hillas[((hillas["Emc_log"] >= binning[i]) & (hillas["Emc_log"] <= binning[i + 1]))]
			elif label=="Core":
				hillas_selected =   hillas[((hillas["core_dist"] >= binning[i]) & (hillas["core_dist"] <= binning[i + 1]))]

			label_entry = "{} events in ({:.2f}, {:.2f})".format(len(hillas_selected), binning[i], binning[i+1])

			ax = fig.add_subplot(111)
			ax.tick_params("both", labelsize=10)
			ax.hist(np.log10(hillas_selected["size"]), range=range_size, bins=80,
				histtype='step', label=label_entry, log=True, linewidth=2, alpha=0.6)

		ax.set_xlabel("log(Size) / phe", fontsize=15)
		ax.set_ylabel("Number of images", fontsize=15)
		ax.legend(fontsize=15)
		if label=="Energy":
			plt.title("Size in dependency of energy", fontsize=17)
		elif label=="Core":
			plt.title("Size in dependency of core distance", fontsize=17)
		#plt.title("{} events: ({:.3f}, {:.3f})".format(len(h), binning[i], binning[i+1]), fontsize=17)
		plt.tight_layout()
		plt.style.use("default")
		plt.savefig(save+"_size_{}_.pdf".format(label[:4]))
		plt.close()

	#############################################################

	for binning, label in zip([ebins, cbins], ["Energy", "Core"]):
		for cam in cams:
			hillas_cam = hillas[hillas["camera"]==cam]
			fig = plt.figure(figsize=[7,6])
			ax = fig.add_subplot(111)
			for i in range(len(ebins) - 1):
				if label=="Energy":
					hillas_selected = hillas_cam[((hillas_cam["Emc_log"] >= binning[i]) & (hillas_cam["Emc_log"] <= binning[i + 1]))]
				elif label=="Core":
					hillas_selected = hillas_cam[((hillas_cam["core_dist"] >= binning[i]) & (hillas_cam["core_dist"] <= binning[i + 1]))]

				label_entry = "Camera {}: {} events in ({:.2f}, {:.2f})".format(cam, len(hillas_selected), binning[i], binning[i+1])
								
				ax.tick_params("both", labelsize=10)
				ax.hist(np.log10(hillas_selected["size"]), range=range_size, bins=80,
					histtype='step', label=label_entry, log=True, linewidth=2, alpha=0.6)

			ax.set_xlabel("log(Size) / phe", fontsize=15)
			ax.set_ylabel("Number of images", fontsize=15)
			ax.legend(fontsize=15)
			if label=="Energy":
				plt.title("Size in dependency of energy", fontsize=17)
			elif label=="Core":
				plt.title("Size in dependency of core distance", fontsize=17)
			#plt.title("{} events: ({:.3f}, {:.3f})".format(len(h), binning[i], binning[i+1]), fontsize=17)
			plt.tight_layout()
			plt.style.use("default")
			plt.savefig(save+"_size_{}_{}_.pdf".format(label[:4], cam))
			plt.close()

	#############################################################

	# comparison of all cameras
	fig = plt.figure(figsize=[7,6])
	ax = fig.add_subplot(111)
	for cam in cams:
		hillas_cam = hillas[hillas["camera"]==cam]

		label_entry = "{}: {} events".format(cam, len(hillas_cam))
							
		ax.tick_params("both", labelsize=10)
		ax.hist(np.log10(hillas_cam["size"]), range=range_size, bins=80, histtype='step',
				label=label_entry, log=True, linewidth=2, alpha=0.8, zorder=2)
	ax.hist(np.log10(hillas["size"]), range=range_size, bins=80, label="All cameras",
		histtype="step", log=True, linewidth=2, alpha=0.6, color='black', zorder=1)
	ax.hist(np.log10(hillas["size"]), range=range_size, bins=80, label=None,
		log=True, alpha=0.1, color='black', zorder=0)
	ax.set_xlabel("log(Size) / phe", fontsize=15)
	ax.set_ylabel("Number of images", fontsize=15)
	ax.legend(fontsize=15)
	
	#plt.title("Size in dependency of energy", fontsize=17)
	#plt.title("{} events: ({:.3f}, {:.3f})".format(len(h), binning[i], binning[i+1]), fontsize=17)
	plt.tight_layout()
	plt.style.use("default")
	plt.savefig(save+"_size_all_cams_.pdf".format(label[:4]))
	plt.close()

	#############################################################
	
	# vs number pixels
	directory = save[:-6]
	os.system("mkdir -p {}/vsnpix".format(directory))
	for cam in cams:
		fig = plt.figure(figsize=[7,6])
		ax = fig.add_subplot(111)

		hillas_cam = hillas[hillas["camera"]==cam]
		ax.tick_params("both", labelsize=10)

		# remove nans
		hillas_cam = hillas_cam.dropna(axis=0)
		
		im = ax.hist2d(np.log10(hillas_cam["size"]), np.log10(hillas_cam["number_pix"]), bins=50, norm=LogNorm(), cmap='viridis')

		ax.set_xlabel("log(size) / phe", fontsize=15)
		ax.set_ylabel("Number of pixels", fontsize=15)
		#fig.colorbar(im, ax=ax)
		plt.colorbar(im[3], ax=ax)
		plt.title("Distribution of size for {}".format(cam), fontsize=17)
		plt.tight_layout()
		plt.style.use("default")
		plt.savefig(directory+"/vsnpix/sizevsPix2D_{}.pdf".format(cam))
		plt.close()

####################################################################################
		####################################################################		
				####################################################													
						####################################		
								####################		
										####		
	if ED:

		for normed in [True, False]:
			# size distribution comparison eventdispla ctapipe for each camera	
			for cam in cams:
				fig = plt.figure(figsize=[7,6])
				ax = fig.add_subplot(111)


				hillas_cam = hillas_cutpix[hillas_cutpix["camera"]==cam]

				MARS_cam = MARS[MARS["size"]>0]
				MARS_cam = MARS_cam[MARS_cam["camera"]==cam]

				ax.tick_params("both", labelsize=10)
				if hyp_stand == "hyper":
					if (cam=="LSTCam"):
						ED_hist = EventDisplay["size_LST"]
					elif (cam=="FlashCam"):
						ED_hist = EventDisplay["size_MSTFC"]
					elif (cam=="DigiCam"):
						ED_hist = EventDisplay["size_SSTDC"]
					elif (cam=="ASTRICam"):
						ED_hist = EventDisplay["size_Astri"]
					elif (cam=="CHEC"):
						ED_hist = EventDisplay["size_SSTGCT"]
					elif (cam=="NectarCam"):
						ED_hist = EventDisplay["size_MSTNC"]
				elif hyp_stand == "standard":
					print(EventDisplay.head())
					if (cam=="LSTCam"):
						ED_hist = EventDisplay["size_LST"]
					elif (cam=="FlashCam"):
						ED_hist = EventDisplay["size_MSTFC"]
					elif (cam=="DigiCam"):
						ED_hist = EventDisplay["size_SSTDC"]
					else:
						continue
						#ED_hist = pd.DataFrame([])	
				
				if not ED_hist.empty:

					histogram = np.array(ED_hist.hists)
					if cam=="LSTCam":
						#sum all 4 bins
						number_to_sum = 2
					else:
						number_to_sum = 2

					if witherr:
						bins_ED, hist_sum, err_sum = change_binning_error(ED_hist, number_to_sum)
					else:
						bins_ED, hist_sum = change_binning(ED_hist, number_to_sum)

					if normed:
						# norm to one
						histnorm = np.sum(hist_sum[~np.isnan(hist_sum)])
						hist_sum = hist_sum / histnorm
					else:
						histnorm = 1

					# for fill between
					alpha = 0.4

					#EventDisplay
					ax.plot(bins_ED, hist_sum, ls='steps', linewidth=2,
						label="EventDisplay", color="C1", alpha=0.8)


					bins_cta = np.arange(range_size[0], range_size[1] + (number_to_sum * ED_hist.width[0]),
										number_to_sum * ED_hist.width[0])
					if normed:
						#ctapipe
						ax.hist(np.log10(hillas_cam["size"]), bins=bins_cta, histtype='step', label="ctapipe",
							log=True, linewidth=2, alpha=0.8, zorder=2, color="C0", normed=True)
						# MARS
						ax.hist(np.log10(MARS_cam["size"]), bins=bins_cta, histtype='step', label="MARS",
							log=True, linewidth=2, alpha=0.8, zorder=2, color="C2", normed=True)
					else:
						# errors for eventdisplay
						plt.fill_between(bins_ED, hist_sum+np.sqrt(hist_sum), hist_sum-np.sqrt(hist_sum), color="C1", alpha=alpha, step="pre")
						#ctapipe
						n, bins, p = ax.hist(np.log10(hillas_cam["size"]), bins=bins_cta, histtype='step', label="ctapipe",
							log=True, linewidth=2, alpha=0.8, zorder=2, color="C0")
						# stat errors
						print_stat_error(bins, n, color="C0", alpha=alpha, add=True, normed=normed)
						# MARS
						n, bins, p = ax.hist(np.log10(MARS_cam["size"]), bins=bins_cta, histtype='step', label="MARS",
							log=True, linewidth=2, alpha=0.8, zorder=2, color="C2")
						# stat errors
						print_stat_error(bins, n, color="C2", alpha=alpha, add=True, normed=normed)

				else:
					x.hist(np.log10(hillas_cam["size"]), range=range_size, bins=80, histtype='step', label="ctapipe",
							log=True, linewidth=2, alpha=0.8, zorder=2, color="C0")
					print_stat_error(bins, n, color="C2", alpha=alpha)

				ax.set_xlabel("log(size) / phe", fontsize=15)
				if normed:
					ax.set_ylabel("Frequency", fontsize=15)
				else:
					ax.set_ylabel("Number of images", fontsize=15)
				ax.legend(fontsize=15)
				plt.title("Distribution of size for {}".format(cam), fontsize=17)
				plt.tight_layout()
				plt.style.use("default")
				if normed:
					plt.savefig(compare+"_size_{}_cutpix_normed.pdf".format(cam))
				else:
					plt.savefig(compare+"_size_{}_cutpix.pdf".format(cam))					
				plt.close()


#######################################################################################
#######################################################################################
#######################################################################################


	#####		###	 ##########	   ###  ###		 ###
	######		###	 ###	 ###   ###	 ###	###
	### ###		###	 ###	  ###  ###	  ###  ###
	###  ###	###	 ###	 ###   ###	   ######
	###	  ###	###	 #########	   ###		####
	###	   ###	###	 ###		   ###	   ######
	###		### ###	 ###		   ###	  ###  ###
	###		 ######	 ###		   ###	 ###	###
	###		  #####	 ###		   ###  ###		 ###

	for binning, label in zip([ebins, cbins], ["Energy", "Core"]):
		fig = plt.figure(figsize=[7,6])
		for i in range(len(ebins) - 1):
			if label=="Energy":
				hillas_selected = hillas[((hillas["Emc_log"] >= binning[i]) & (hillas["Emc_log"] <= binning[i + 1]))]
			elif label=="Core":
				hillas_selected =   hillas[((hillas["core_dist"] >= binning[i]) & (hillas["core_dist"] <= binning[i + 1]))]

			label_entry = "{} events in ({:.2f}, {:.2f})".format(len(hillas_selected), binning[i], binning[i+1])

			ax = fig.add_subplot(111)
			ax.tick_params("both", labelsize=10)
			ax.hist(hillas_selected["number_pix"], range=range_pix, bins=40,
				histtype='step', label=label_entry, log=True, linewidth=2, alpha=0.6)

		ax.set_xlabel("log(Number of pixels)", fontsize=15)
		ax.set_ylabel("Number of images", fontsize=15)
		ax.legend(fontsize=15)
		if label=="Energy":
			plt.title("Number of pixels in dependency of energy", fontsize=17)
		elif label=="Core":
			plt.title("Number of pixels in dependency of core distance", fontsize=17)
		plt.tight_layout()
		plt.style.use("default")
		plt.savefig(save+"_nPixel_{}_.pdf".format(label[:4]))
		plt.close()


	for binning, label in zip([ebins, cbins], ["Energy", "Core"]):
		for cam in cams:
			hillas_cam = hillas[hillas["camera"]==cam]
			fig = plt.figure(figsize=[7,6])
			ax = fig.add_subplot(111)
			for i in range(len(ebins) - 1):
				if label=="Energy":
					hillas_selected = hillas_cam[((hillas_cam["Emc_log"] >= binning[i]) & (hillas_cam["Emc_log"] <= binning[i + 1]))]
				elif label=="Core":
					hillas_selected = hillas_cam[((hillas_cam["core_dist"] >= binning[i]) & (hillas_cam["core_dist"] <= binning[i + 1]))]

				label_entry = "Camera {}: {} events in ({:.2f}, {:.2f})".format(
							cam, len(hillas_selected), binning[i], binning[i+1])
								
				ax.tick_params("both", labelsize=10)
				ax.hist(hillas_selected["number_pix"], range=range_pix,
						bins=40, histtype='step', label=label_entry, log=True,
						linewidth=2, alpha=0.6)

			ax.set_xlabel("log(Number of pixels)", fontsize=15)
			ax.set_ylabel("Number of images", fontsize=15)
			ax.legend(fontsize=15)
			if label=="Energy":
				plt.title("Number of pixels in dependency of energy", fontsize=17)
			elif label=="Core":
				plt.title("Number of pixels in dependency of core distance", fontsize=17)
			#plt.title("{} events: ({:.3f}, {:.3f})".format(len(h), binning[i], binning[i+1]), fontsize=17)
			plt.tight_layout()
			plt.style.use("default")
			plt.savefig(save+"_nPixel_{}_{}_.pdf".format(label[:4], cam))
			plt.close()

	# comparison of all cameras
	fig = plt.figure(figsize=[7,6])
	ax = fig.add_subplot(111)
	for cam in cams:
		hillas_cam = hillas[hillas["camera"]==cam]

		label_entry = "{}: {} events".format(cam, len(hillas_cam))
							
		ax.tick_params("both", labelsize=10)
		ax.hist(hillas_cam["number_pix"], range=range_pix, bins=40,
			histtype='step', label=label_entry, log=True, linewidth=2,
			alpha=0.8, zorder=2)
	ax.hist(hillas["number_pix"], range=range_pix, bins=40,
			label="All cameras", histtype="step", log=True, linewidth=2,
			alpha=0.6, color='black', zorder=1)
	ax.hist(hillas["number_pix"], range=range_pix, bins=40,
			label=None, log=True, alpha=0.1, color='black', zorder=0)

	ax.set_xlabel("Number of pixels", fontsize=15)
	ax.set_ylabel("Number of images", fontsize=15)
	ax.legend(fontsize=15)
	
	#plt.title("Size in dependency of energy", fontsize=17)
	#plt.title("{} events: ({:.3f}, {:.3f})".format(len(h), binning[i], binning[i+1]), fontsize=17)
	plt.tight_layout()
	plt.style.use("default")
	plt.savefig(save+"_nPixel_all_cams_.pdf")
	plt.close()


####################################################################################
		####################################################################		
				####################################################													
						####################################		
								####################		
										####		
	if ED:
		for normed in [True, False]:
			# comparison of all cameras
			fig = plt.figure(figsize=[7,6])
			ax = fig.add_subplot(111)
			# histogram of Eventdisplay
			ED_hist = EventDisplay['ntubes_per_image']
			"""
			# change binning
			histogram = np.array(ED_hist.hists)
			number_to_sum = 8
			hist_sum = None
			for k in range(number_to_sum):
				try:
					entries = len(histogram[k::number_to_sum])
					if entries == len(hist_sum):
						hist_sum = hist_sum + histogram[k::number_to_sum]
					else:
						hist_sum = hist_sum[:entries] + histogram[k::number_to_sum]
				except (NameError, TypeError):
					hist_sum = histogram[::number_to_sum]

			hist_sum = np.append(hist_sum[0], hist_sum)
			hist_sum = np.append(0, hist_sum)
			bins_ED =  np.append(ED_hist.bins[0], ED_hist.bins[::number_to_sum])
			"""
			number_to_sum = 120
			if witherr:
				bins_ED, hist_sum, err_sum = change_binning_error(ED_hist, number_to_sum)
			else:
				bins_ED, hist_sum = change_binning(ED_hist, number_to_sum)

			if normed:
				# norm to one
				hist_sum = hist_sum / np.sum(hist_sum[~np.isnan(hist_sum)])

			# EventDisplay
			ax.plot(bins_ED, hist_sum, ls='steps', linewidth=2,
				label="EventDisplay", alpha=0.8, color="C1")


			bins_cta = np.arange(np.min(hillas["number_pix"]), np.max(hillas["number_pix"]) + (number_to_sum * ED_hist.width[0]),
											number_to_sum * ED_hist.width[0])
			if normed:
				# ctapipe
				n, bins, p = ax.hist(hillas["number_pix"], bins=bins_cta, normed=True, label="ctapipe",
					histtype="step", log=True, linewidth=2, alpha=0.6, zorder=1, color="C0")
				# MARS
				n, bins, p = ax.hist(MARS["numUsedPix"], bins=bins_cta, normed=True, label="MARS",
					histtype="step", log=True, linewidth=2, alpha=0.6, zorder=1, color="C2")
			else:						
				# errors for eventdisplay
				plt.fill_between(bins_ED, hist_sum+np.sqrt(hist_sum), hist_sum-np.sqrt(hist_sum), color="C1", alpha=alpha, step="pre")
				# ctapipe
				n, bins, p = ax.hist(hillas["number_pix"], bins=bins_cta, label="ctapipe", histtype="step",
					log=True, linewidth=2, alpha=0.6, zorder=1, color="C0")
				print_stat_error(bins, n, color="C0", alpha=alpha)
				# MARS
				n, bins, p = ax.hist(MARS["numUsedPix"], bins=bins_cta, label="MARS", histtype="step",
					log=True, linewidth=2, alpha=0.6, zorder=1, color="C2")
				print_stat_error(bins, n, color="C2", alpha=alpha)

			ax.set_xlabel("Number of pixels", fontsize=15)
			if normed:
				ax.set_ylabel("Frequency", fontsize=15)
			else:
				ax.set_ylabel("Number of images", fontsize=15)
			ax.legend(fontsize=15)
			plt.tight_layout()
			plt.style.use("default")
			if normed:
				plt.savefig(compare+"_nPixel_all_normed.pdf")
			else:
				plt.savefig(compare+"_nPixel_all.pdf")
			plt.close()

		"""
		# Apply sizecuts
		for size in [100,150,200]:
			# comparison of all cameras with sizecut in ctapipe
			fig = plt.figure(figsize=[7,6])
			ax = fig.add_subplot(111)

			# only size > 100
			hillas_size = hillas[hillas["size"]>size]

			ax.hist(hillas["number_pix"], bins=np.arange(np.max(hillas["number_pix"])),
					label="ctapipe", log=True, alpha=0.1, color='C0', zorder=0)
			ax.hist(hillas_size["number_pix"], bins=np.arange(np.max(hillas["number_pix"])),
					label="ctapipe, size>{}".format(size), histtype="step", log=True,
					linewidth=2, alpha=0.6, zorder=1 , color='C0')
			# histogram of Eventdisplay
			ED_hist = EventDisplay['ntubes_per_image']
			ax.plot(ED_hist.bins, ED_hist.hists, ls='steps', linewidth=2,
					label="EventDisplay",color="C1", alpha=0.8)

			ax.set_xlabel("Number of pixels", fontsize=15)
			ax.set_ylabel("Number of images", fontsize=15)
			ax.legend(fontsize=15)

			plt.tight_layout()
			plt.style.use("default")
			#plt.savefig(compare+"_nPixel_all_sizecut{}.pdf".format(size))
			plt.close()
		"""

		for normed in [True, False]:
			# One plot per Energy bin:
			for i, EDisp in zip(range(len(ebins) - 1), ["ntubes_per_image_ebin1","ntubes_per_image_ebin2",
												 "ntubes_per_image_ebin3","ntubes_per_image_ebin4"]):
				ED_hist = EventDisplay[EDisp]

				hillas_selected = hillas[((hillas["Emc_log"] >= ebins[i]) & (hillas["Emc_log"] <= ebins[i + 1]))]
				title_entry = "Energy range from ({:.2f}, {:.2f})".format(ebins[i], ebins[i+1])
				MARS_selected = MARS[((MARS["Emc_log"] >= ebins[i]) & (MARS["Emc_log"] <= ebins[i + 1]))]

				"""
				# change binning
				histogram = np.array(ED_hist.hists)
				number_to_sum = 4
				hist_sum = None
				for k in range(number_to_sum):
					try:
						entries = len(histogram[k::number_to_sum])
						if entries == len(hist_sum):
							hist_sum = hist_sum + histogram[k::number_to_sum]
						else:
							hist_sum = hist_sum[:entries] + histogram[k::number_to_sum]
					except (NameError, TypeError):
						hist_sum = histogram[::number_to_sum]

				hist_sum = np.append(hist_sum[0], hist_sum)
				hist_sum = np.append(0, hist_sum)
				bins_ED =  np.append(ED_hist.bins[0], ED_hist.bins[::number_to_sum])
				"""

				if max(hillas_selected["number_pix"]) > 1000:
					number_to_sum = 30
				elif max(hillas_selected["number_pix"]) > 500:
					number_to_sum = 15
				else:
					number_to_sum = 15
				if witherr:
					bins_ED, hist_sum, err_sum = change_binning_error(ED_hist, number_to_sum)
				else:
					bins_ED, hist_sum = change_binning(ED_hist, number_to_sum)

				if normed:
					# norm to one
					hist_sum = hist_sum / np.sum(hist_sum[~np.isnan(hist_sum)])

				bins_cta = np.arange(np.min(hillas_selected["number_pix"]),
					np.max(hillas_selected["number_pix"]) + (number_to_sum * ED_hist.width[0]),
					number_to_sum * ED_hist.width[0])

				fig = plt.figure(figsize=[7,6])
				ax = fig.add_subplot(111)
				ax.tick_params("both", labelsize=10)
				ax.plot(bins_ED, hist_sum, ls='steps', linewidth=2,
						label="EventDisplay", color="C1", alpha=0.8)

				if normed:
					ax.hist(hillas_selected["number_pix"], bins=bins_cta, histtype='step', label="ctapipe",
						log=True, linewidth=2, alpha=0.6, color="C0", normed=True)
					try:
						ax.hist(MARS_selected["numUsedPix"], bins=bins_cta,	histtype='step', label="ctapipe",
							log=True, linewidth=2, alpha=0.6, color="C2", normed=True)
					except ValueError:
						pass
				else:						
					# errors for eventdisplay
					plt.fill_between(bins_ED, hist_sum+np.sqrt(hist_sum), hist_sum-np.sqrt(hist_sum), color="C1", alpha=alpha, step="pre")

					n, bins, p = ax.hist(hillas_selected["number_pix"], bins=bins_cta, histtype='step', label="ctapipe",
						log=True, linewidth=2, alpha=0.6, color="C0")
					print_stat_error(bins, n, color="C0", alpha=alpha)
					n, bins, p = ax.hist(MARS_selected["numUsedPix"], bins=bins_cta,	histtype='step', label="MARS",
						log=True, linewidth=2, alpha=0.6, color="C2")
					print_stat_error(bins, n, color="C2", alpha=alpha)


				ax.set_xlabel("Number of pixels", fontsize=15)
				if normed:
					ax.set_ylabel("Frequency", fontsize=15)
				else:
					ax.set_ylabel("Number of images", fontsize=15)
				ax.legend(fontsize=15)

				if max(hillas_selected["number_pix"]) > 1000:
					pass
				elif max(hillas_selected["number_pix"]) > 500:
					ax.set_xlim(ax.get_xlim()[0], 750)
				else:
					number_to_sum = 15
					ax.set_xlim(-30, 280)

				plt.title(title_entry, fontsize=17)
				plt.tight_layout()
				plt.style.use("default")
				if normed:
					plt.savefig(compare+"_nPixel_Energy_{}_{}_normed.pdf".format(ebins[i], ebins[i+1]))
				else:
					plt.savefig(compare+"_nPixel_Energy_{}_{}.pdf".format(ebins[i], ebins[i+1]))
				plt.close()

			'''
			# One plot per core bin:
			for i, EDisp in zip(range(len(cbins) - 1), ["ntubes_per_image_corebin1","ntubes_per_image_corebin2",
												 "ntubes_per_image_corebin3","ntubes_per_image_corebin4"]):
				ED_hist = EventDisplay[EDisp]

				number_to_sum = 10
				if witherr:
					bins_ED, hist_sum, err_sum = change_binning_error(ED_hist, number_to_sum)
				else:
					bins_ED, hist_sum = change_binning(ED_hist, number_to_sum)
				
				if normed:
					# norm to one
					hist_sum = hist_sum / np.sum(hist_sum[~np.isnan(hist_sum)])

				hillas_selected = hillas[((hillas["core_dist"] >= cbins[i]) & (hillas["core_dist"] <= cbins[i + 1]))]
				title_entry = "core range from ({:.2f}, {:.2f})".format(cbins[i], cbins[i+1])
				MARS_selected = MARS[((MARS["core_dist"] >= cbins[i]) & (MARS["core_dist"] <= cbins[i + 1]))]

				bins_cta = np.arange(np.min(hillas["number_pix"]),
						np.max(hillas["number_pix"]) + (number_to_sum * ED_hist.width[0]),
						number_to_sum * ED_hist.width[0])

				fig = plt.figure(figsize=[7,6])
				ax = fig.add_subplot(111)
				ax.tick_params("both", labelsize=10)

				ax.plot(ED_hist.bins, ED_hist.hists, ls='steps', linewidth=2,
						label="EventDisplay", color="C1", alpha=0.8)
				print("-----------")
				print(np.max(hillas_selected["number_pix"]))
				print(np.arange(np.max(hillas_selected["number_pix"])))
				print(bins_cta)
				print("-----------")

				if normed:

					ax.hist(hillas_selected["number_pix"], bins=bins_cta, normed=True,
							histtype='step', label="ctapipe", log=True, linewidth=2, alpha=0.6, color="C0")
					ax.hist(MARS_selected["numUsedPix"], bins=bins_cta, normed=True,
							histtype='step', label="MARS", log=True, linewidth=2, alpha=0.6, color="C2")
				else:					
					# errors for eventdisplay
					plt.fill_between(bins_ED, hist_sum+np.sqrt(hist_sum), hist_sum-np.sqrt(hist_sum), color="C1", alpha=alpha, step="pre")

					n, bins, p = ax.hist(hillas_selected["number_pix"], bins=bins_cta, normed=True,
							histtype='step', label="ctapipe", log=True, linewidth=2, alpha=0.6, color="C0")
					print_stat_error(bins, n, color="C2", alpha=alpha)
					n, bins, p = ax.hist(MARS_selected["numUsedPix"], bins=bins_cta, normed=True,
							histtype='step', label="MARS", log=True, linewidth=2, alpha=0.6, color="C2")
					print_stat_error(bins, n, color="C2", alpha=alpha)

				ax.set_xlabel("Number of pixels", fontsize=15)
				if normed:
					ax.set_ylabel("Frequency", fontsize=15)
				else:
					ax.set_ylabel("Number of images", fontsize=15)
				ax.legend(fontsize=15)

				plt.title(title_entry, fontsize=17)
				plt.tight_layout()
				plt.style.use("default")
				if normed:
					plt.savefig(compare+"_nPixel_core_{}_{}_normed.pdf".format(cbins[i], cbins[i+1]))
				else:
					plt.savefig(compare+"_nPixel_core_{}_{}.pdf".format(cbins[i], cbins[i+1]))
				plt.close()
			'''
			# number of pixels distribution comparison eventdispla ctapipe for each camera	
			for cam in cams:
				fig = plt.figure(figsize=[7,6])
				ax = fig.add_subplot(111)


				hillas_cam = hillas[hillas["camera"]==cam]
				MARS_cam = MARS[MARS["camera"]==cam]
				ax.tick_params("both", labelsize=10)
				
				if (cam=="LSTCam"):
					ED_hist = EventDisplay["ntubes_per_image_LST"]
				elif (cam=="FlashCam"):
					ED_hist = EventDisplay["ntubes_per_image_MSTFC"]
				elif (cam=="DigiCam"):
					ED_hist = EventDisplay["ntubes_per_image_SSTDC"]
				elif (cam=="NectarCam"):
					ED_hist = EventDisplay["ntubes_per_image_MSTNC"]
				elif (cam=="CHEC"):
					ED_hist = EventDisplay["ntubes_per_image_SSTGCT"]
				else:
					ED_hist = pd.DataFrame([])	

				if not ED_hist.empty:
					number_to_sum = 30
					if witherr:
						bins_ED, hist_sum, err_sum = change_binning_error(ED_hist, number_to_sum)
					else:
						bins_ED, hist_sum = change_binning(ED_hist, number_to_sum)

<<<<<<< HEAD
					print("--------------------{}-----------------------------".format(cam))
					print("{}".format(np.array(hist_sum)[~np.isnan(hist_sum)]))
					print(ED_hist.head(30))

=======
>>>>>>> 507fdcf53c4464f4822d763ecffe7109305ed0d6
					if normed:
						# norm to one
						hist_sum = hist_sum / np.sum(hist_sum[~np.isnan(hist_sum)])

					# adapt binning to eventdisplay
					bins_cta = np.arange(np.min(hillas["number_pix"]),
						np.max(hillas["number_pix"]) + (number_to_sum * ED_hist.width[0]),
						number_to_sum * ED_hist.width[0])

					ax.plot(bins_ED, hist_sum, ls='steps', linewidth=2,
							label="EventDisplay", color="C1", alpha=0.8)

					if normed:
						ax.hist(hillas_cam["number_pix"], bins=bins_cta, histtype='step', label="ctapipe",
							log=True, linewidth=2, alpha=0.8, zorder=2, color="C0", normed=True)
						ax.hist(MARS_cam["numUsedPix"], bins=bins_cta, histtype='step', label="MARS",
							log=True, linewidth=2, alpha=0.8, zorder=2, color="C2", normed=True)
					else:
						plt.fill_between(bins_ED, hist_sum+np.sqrt(hist_sum), hist_sum-np.sqrt(hist_sum), color="C1", alpha=alpha, step="pre")

						n, bins, p = ax.hist(hillas_cam["number_pix"], bins=bins_cta, histtype='step', label="ctapipe",
							log=True, linewidth=2, alpha=0.8, zorder=2, color="C0")
						print_stat_error(bins, n, color="C0", alpha=alpha)
						n, bins, p = ax.hist(MARS_cam["numUsedPix"], bins=bins_cta, histtype='step', label="MARS",
							log=True, linewidth=2, alpha=0.8, zorder=2, color="C2")
						print_stat_error(bins, n, color="C2", alpha=alpha)
				else:
					continue

				ax.set_xlabel("Number of pixels", fontsize=15)
				if normed:
					ax.set_ylabel("Frequency", fontsize=15)
				else:
					ax.set_ylabel("Number of images", fontsize=15)
				ax.legend(fontsize=15)
				plt.title("Number of pixels for {}".format(cam), fontsize=17)
				plt.tight_layout()
				plt.style.use("default")
				if normed:
					plt.savefig(compare+"_nPixel_{}_normed.pdf".format(cam))
				else:
					plt.savefig(compare+"_nPixel_{}.pdf".format(cam))
				plt.close()


#######################################################################################
#######################################################################################
#######################################################################################

	###		 ###	  ###	     ### ###
	###		#####	  ###	    ###	 ###
	###	   ### ###	  ###	   ###	 ###
	###   ###   ###	  ###	  ###	 ###
	###  ###	 ###  ###	 ###	 ###
	###	###		  ### ###	###		 ###
	######		   ######  ###		 ##############
	#####			##### ###		 ##############

	###############################
	# width / length vs core_dist #
	###############################


	# length / width for all bins in one plot
	for lw, range_lw in zip(["length", "width"], [range_length, range_width]):
		for binning, label in zip([ebins, cbins], ["Energy", "Core"]):
			fig = plt.figure(figsize=[7,6])
			ax = fig.add_subplot(111)
			for i in range(len(ebins) - 1):
				if label=="Energy":
					hillas_selected = hillas[((hillas["Emc_log"] >= binning[i]) & (hillas["Emc_log"] <= binning[i + 1]))]
				elif label=="Core":
					hillas_selected =   hillas[((hillas["core_dist"] >= binning[i]) & (hillas["core_dist"] <= binning[i + 1]))]

				label_entry = "{} events in ({:.2f}, {:.2f})".format(len(hillas_selected), binning[i], binning[i+1])
				ax.tick_params("both", labelsize=10)

				ax.hist(hillas_selected[lw] * hillas_selected["mtodeg"], range=range_lw, bins=80, histtype='step',
						label=label_entry, log=True, linewidth=2, alpha=0.6)

			ax.set_xlabel("length, width / deg", fontsize=15)
			ax.set_ylabel("Number of images", fontsize=15)
			ax.legend(fontsize=15)
			if label=="Energy":
				plt.title("{} in dependency of energy".format(lw), fontsize=17)
			elif label=="Core":
				plt.title("{} in dependency of core distance".format(lw), fontsize=17)
			#plt.title("{} events: ({:.3f}, {:.3f})".format(len(h), binning[i], binning[i+1]), fontsize=17)
			plt.tight_layout()
			plt.style.use("default")
			plt.savefig(save+"_length_width_{}_.pdf".format(label[:4]))
			plt.close()

	# length and width for complete range in one plot
	for binning, label in zip([ebins, cbins], ["Energy", "Core"]):
		for i in range(len(ebins) - 1):
			if label=="Energy":
				hillas_selected = hillas[((hillas["Emc_log"] >= binning[i]) & (hillas["Emc_log"] <= binning[i + 1]))]
			elif label=="Core":
				hillas_selected = hillas[((hillas["core_dist"] >= binning[i]) & (hillas["core_dist"] <= binning[i + 1]))]
			fig = plt.figure(figsize=[7,6])
			ax = fig.add_subplot(111)
		
			ax.tick_params("both", labelsize=10)
			for lw in ["length", "width"]:
				ax.hist(hillas_selected[lw] * hillas_selected["mtodeg"], range=range_lengthwidth, bins=80, histtype='step',
						label=lw, log=True, linewidth=2, alpha=0.6)
				if label=="Energy":
					plt.title("Length and width in dependency of energy".format(lw), fontsize=17)
				elif label=="Core":
					plt.title("Length and width in dependency of core distance".format(lw), fontsize=17)

			ax.set_xlabel("{} / deg".format(lw), fontsize=15)
			ax.set_ylabel("Number of images", fontsize=15)
			ax.legend(fontsize=15)

			plt.title("{} events: ({:.2f}, {:.2f})".format(len(hillas_selected),
										 binning[i], binning[i+1]), fontsize=17)
			plt.tight_layout()
			plt.style.use("default")
			plt.savefig(save+"_length_width_{}_{:.0f}_{:.0f}_.pdf".format(
										label[:4], binning[i], binning[i+1]))
			plt.close()


	for lw, range_lw in zip(["length", "width"], [range_length, range_width]):
		# comparison of all cameras
		fig = plt.figure(figsize=[7,6])
		ax = fig.add_subplot(111)
		for cam in cams:
			hillas_cam = hillas[hillas["camera"]==cam]

			label_entry = "{}: {} events".format(cam, len(hillas_cam))
								
			ax.tick_params("both", labelsize=10)
			ax.hist(hillas_cam[lw] * hillas_cam["mtodeg"], range=range_lw, bins=80, histtype='step',
				label=label_entry, log=True, linewidth=2, alpha=0.8, zorder=2)
		ax.hist(hillas[lw], range=range_lw, bins=80, label="All cameras",
			histtype="step", log=True, linewidth=2, alpha=0.6, color='black',
			zorder=1)
		ax.hist(hillas[lw] *  hillas["mtodeg"], range=range_lw, bins=80, label=None, log=True,
			alpha=0.1, color='black', zorder=0)
		ax.set_xlabel("{} / deg".format(lw), fontsize=15)
		ax.set_ylabel("Number of images", fontsize=15)
		ax.legend(fontsize=15)
		
		#plt.title("Size in dependency of energy", fontsize=17)
		#plt.title("{} events: ({:.3f}, {:.3f})".format(len(h), binning[i], binning[i+1]), fontsize=17)
		plt.tight_layout()
		plt.style.use("default")
		plt.savefig(save+"_length_width_{}_all_cams_.pdf".format(lw))
		plt.close()

	# Flashcam only with sizecut
	for size in [100]:
		fig = plt.figure(figsize=[7,6])
		ax = fig.add_subplot(111)
		for lw, range_lw, color in zip(["length", "width"], [range_length, range_width], ["C0", "C1"]):
			# comparison of all cameras
			for cam in ["FlashCam"]:
				hillas_cam = hillas[hillas["camera"]==cam]

				hillas_cam_size = hillas_cam[hillas_cam["size"] > size]
				label_entry = "{} events, {}".format(len(hillas_cam), lw)
				label_entry_size = "{} events, size>{}, {}".format(
					len(hillas_cam_size), size, lw)

				ax.tick_params("both", labelsize=10)
				ax.hist(hillas_cam[lw] * hillas_cam["mtodeg"], range=range_lw, bins=80, histtype='step',
					label=label_entry, log=True, ls="-", linewidth=2, alpha=0.6,
					zorder=2, color=color)
				ax.hist(hillas_cam_size[lw] * hillas_cam_size["mtodeg"], range=range_lw, bins=80, histtype='step',
					label=label_entry_size, ls=":", log=True, linewidth=2, alpha=0.8,
					zorder=2, color=color)

		ax.set_xlabel("length, width / deg".format(lw), fontsize=15)
		ax.set_ylabel("Number of images", fontsize=15)
		ax.legend(fontsize=15)
		plt.tight_layout()
		plt.style.use("default")
		plt.savefig(save+"_length_width_FlashCam_Size{}.pdf".format(size))
		plt.close()


############# vs number of pixels
	for lw, range_lw in zip(["length", "width"], [range_length, range_width]):
		# comparison of eventdisplay and ctapipe for each camera
		for cam in cams:
			fig = plt.figure(figsize=[7,6])
			ax = fig.add_subplot(111)

			hillas_cam = hillas[hillas["camera"]==cam]
			ax.tick_params("both", labelsize=10)

			# remove nans
			hillas_cam = hillas_cam.dropna(axis=0)
			lenwid = hillas_cam[lw] * hillas_cam["mtodeg"]
			im = ax.hist2d(lenwid, hillas_cam["number_pix"], bins=80, norm=LogNorm(), cmap='viridis')

			ax.set_xlabel("{} / deg".format(lw), fontsize=15)
			ax.set_ylabel("Number of pixels", fontsize=15)
			#fig.colorbar(im, ax=ax)
			plt.colorbar(im[3], ax=ax)
			plt.title("Distribution of {} for {}".format(lw, cam), fontsize=17)
			plt.tight_layout()
			plt.style.use("default")
			plt.savefig(directory+"/vsnpix/{}vsPix2D_{}.pdf".format(lw, cam))
			plt.close()

############# small values, vs number of pixels
	# doesn't work for highNSB (and this doesn't have ED...)
	if ED:
		for lw, range_lw in zip(["length", "width"], [range_length, range_width]):
			# comparison of eventdisplay and ctapipe for each camera
			for cam in cams:
				fig = plt.figure(figsize=[7,6])
				ax = fig.add_subplot(111)

				hillas_cam = hillas[hillas["camera"]==cam]
				hillas_cam = hillas_cam[(hillas_cam[lw] * hillas_cam["mtodeg"])<0.15]
				ax.tick_params("both", labelsize=10)

				# remove nans
				hillas_cam = hillas_cam.dropna(axis=0)
				lenwid = hillas_cam[lw] * hillas_cam["mtodeg"]
				number_bins_hist = np.max(hillas_cam["number_pix"])
				if (number_bins_hist > 50) & (number_bins_hist <= 100):
					number_bins_hist = int(number_bins_hist/2)
				elif (number_bins_hist > 100) & (number_bins_hist <= 200):
					number_bins_hist = int(number_bins_hist/4)
				elif (number_bins_hist > 200):
					number_bins_hist = int(number_bins_hist/4)

				im = ax.hist2d(lenwid, hillas_cam["number_pix"], bins=[15,number_bins_hist], norm=LogNorm(), cmap='viridis')

				ax.set_xlabel("{} / deg".format(lw), fontsize=15)
				ax.set_ylabel("Number of pixels", fontsize=15)
				#fig.colorbar(im, ax=ax)
				plt.colorbar(im[3], ax=ax)
				plt.title("Distribution of {} for {}".format(lw, cam), fontsize=17)
				plt.tight_layout()
				plt.style.use("default")
				plt.savefig(directory+"/vsnpix/{}vsPix2D_{}_small.pdf".format(lw, cam))
				plt.close()

			'''
			fig = plt.figure(figsize=[7,6])
			ax = fig.add_subplot(111)

			hillas_cam = hillas[hillas["camera"]==cam]
			hillas_cam = hillas[hillas[lw]<0.15]
			ax.tick_params("both", labelsize=10)

			ax.hist(hillas_cam["number_pix"], bins=30,
					log=True, linewidth=2, alpha=0.8, zorder=2)

			ax.set_xlabel("Number pixels".format(lw), fontsize=15)
			ax.set_ylabel("Number of images", fontsize=15)
			plt.title("Distribution of {} for {}".format(lw, cam), fontsize=17)
			plt.tight_layout()
			plt.style.use("default")
			plt.savefig(directory+"/vsnpix/{}vsPix_{}.pdf".format(lw, cam))
			plt.close()
			'''



####################################################################################
		####################################################################		
				####################################################													
						####################################		
								####################		
										####


	if ED:
		for logarithmic in [True, False]:
			# LSTCam ASTRICam CHEC DigiCam FlashCam NectarCam
			for normed in [True, False]:
				for lw, range_lw in zip(["length", "width"], [range_length, range_width]):
					# comparison of eventdisplay and ctapipe for each camera
					for cam in cams:
						fig = plt.figure(figsize=[7,6])
						ax = fig.add_subplot(111)

						hillas_cam = hillas_cutpix[hillas_cutpix["camera"]==cam]
						MARS_cam = MARS[MARS["camera"]==cam]

						ax.tick_params("both", labelsize=10)
						
						if hyp_stand == "hyper":
							if (cam=="LSTCam"):
								ED_hist = EventDisplay["{}_LST".format(lw)]
							elif (cam=="FlashCam"):
								ED_hist = EventDisplay["{}_MSTFC".format(lw)]
							elif (cam=="DigiCam"):
								ED_hist = EventDisplay["{}_SSTDC".format(lw)]
							elif (cam=="ASTRICam"):
								ED_hist = EventDisplay["{}_Astri".format(lw)]
							elif (cam=="CHEC"):
								ED_hist = EventDisplay["{}_SSTGCT".format(lw)]
							elif (cam=="NectarCam"):
								ED_hist = EventDisplay["{}_MSTNC".format(lw)]

						elif hyp_stand == "standard":
							if (cam=="LSTCam"):
								ED_hist = EventDisplay["{}_LST".format(lw)]
							elif (cam=="FlashCam"):
								ED_hist = EventDisplay["{}_MSTFC".format(lw)]
							elif (cam=="DigiCam"):
								ED_hist = EventDisplay["{}_SSTDC".format(lw)]
							else:
								continue
								#ED_hist = pd.DataFrame([])	

						if not ED_hist.empty:

							# change binning
							if lw == "width":
								number_to_sum = 5
							elif lw == "length":
								number_to_sum = 10
							if witherr:
								bins_ED, hist_sum, err_sum = change_binning_error(ED_hist, number_to_sum)
							else:
								bins_ED, hist_sum = change_binning(ED_hist, number_to_sum)

							if normed: 		
								# norm to one
								hist_sum = hist_sum / np.sum(hist_sum[~np.isnan(hist_sum)])

							ax.plot(bins_ED, hist_sum, ls='steps', linewidth=2,
								label="EventDisplay", color="C1", alpha=0.8)

							# remove nans
							hillas_cam = hillas_cam.dropna(axis=0)
							bins_cta = np.arange(range_lw[0], range_lw[1] + (number_to_sum * ED_hist.width[0]), (number_to_sum * ED_hist.width[0]))

							lenwid = hillas_cam[lw] * hillas_cam["mtodeg"]
							MARS_lenwid = MARS_cam[lw] * MARS_cam["mtodeg"] / 1000

							if normed:
								ax.hist(lenwid, bins=bins_cta, histtype='step', label="ctapipe", normed=True,
										log=logarithmic, linewidth=2, alpha=0.8, zorder=2, color="C0")
								try:
									ax.hist(MARS_lenwid, bins=bins_cta, histtype='step', label="MARS", normed=True,
										log=logarithmic, linewidth=2, alpha=0.8, zorder=2, color="C2")
								except ValueError:
									pass
							else:
								plt.fill_between(bins_ED, hist_sum+np.sqrt(hist_sum), hist_sum-np.sqrt(hist_sum), color="C1", alpha=alpha, step="pre")

								n, bins, p = ax.hist(lenwid, bins=bins_cta, histtype='step', label="ctapipe",
										log=logarithmic, linewidth=2, alpha=0.8, zorder=2, color="C0")
								print_stat_error(bins, n, color="C0", alpha=alpha)
								n, bins, p = ax.hist(MARS_lenwid, bins=bins_cta, histtype='step', label="MARS",
										log=logarithmic, linewidth=2, alpha=0.8, zorder=2, color="C2")
								print_stat_error(bins, n, color="C2", alpha=alpha)
						else:
							continue

						ax.set_xlabel("{} / deg".format(lw), fontsize=15)
						if normed:
							ax.set_ylabel("Frequency", fontsize=15)
						else:
							ax.set_ylabel("Number of images", fontsize=15)
						ax.legend(fontsize=15)
						plt.title("Distribution of {} for {}".format(lw, cam), fontsize=17)
						plt.tight_layout()
						plt.style.use("default")
						if logarithmic:
							loglabel = ""
						else:
							loglabel = "linear"
						if normed:
							plt.savefig(compare+"_{}_{}_cutpix_normed_{}.pdf".format(lw, cam, loglabel))
						else:
							plt.savefig(compare+"_{}_{}_cutpix_{}.pdf".format(lw, cam, loglabel))
						plt.close()


#######################################################################################
#######################################################################################
#######################################################################################
