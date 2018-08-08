import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ctapipe.calib.camera import CameraCalibrator
from konsta_cta.readdata import FileReader

from traitlets.config import Config

def read_EventDisplay(file):
	# read data EventDisplay
	with open(file) as f:
		content = f.readlines()

	data = []
	for line in content:
		row = line.split()
		# check for correct number of entries
		if len(row) != 4:
			continue
		# check if first 3 entries is integer
		try:
			row_number = [ int(x) for x in row[:3] ]
			row_number.append(np.float(row[3]))
		except ValueError:
			continue

		data.append(row_number)

	df = pd.DataFrame(data, columns=[
		"EventID", "TelescopeID", "PixelID", "charge"]	)

	return df

def pick_gain_channel(pmt_signal, cam_id, pe_thresh):
	'''the PMTs on some (most?) cameras have 2 gain channels. select one
	according to a threshold. ultimately, this will be done IN the
	camera/telescope itself but until then, do it here
	'''
	np_true_false = np.array([[True], [False]])
	if pmt_signal.shape[0] > 1:
		pmt_signal = np.squeeze(pmt_signal)
		pick = (pe_thresh[cam_id] <
				pmt_signal).any(axis=0) != np_true_false
		pmt_signal = pmt_signal.T[pick.T]
	else:
		pmt_signal = np.squeeze(pmt_signal)
	return pmt_signal

def analyze_ctapipe():
	print("starting ctapipe.")
	gamma = FileReader("/lustre/fs21/group/cta/prod3b/prod3b-paranal20deg/gamma_onSource/gamma_20deg_0deg_run624___cta-prod3_desert-2150m-Paranal-merged.simtel.gz", "gamma")
	gamma.read_files()

	trace_width = {
		"ASTRICam": (10, 5),
		"FlashCam": (4, 2),
		"LSTCam": (4, 2),
		"NectarCam": (6, 3),
		"DigiCam": (4, 2),
		"CHEC": (8, 4),
		"SCTCam": (6, 3)}

	# from Tino
	pe_thresh = {
		"ASTRICam": 14,
		"LSTCam": 100,
		"NectarCam": 190}

	#integrators = ['GlobalPeakIntegrator', 'LocalPeakIntegrator', 'NeighbourPeakIntegrator', 'AverageWfPeakIntegrator']
	#cleaners = ['NullWaveformCleaner', 'CHECMWaveformCleanerAverage', 'CHECMWaveformCleanerLocal']
	for integrator in ['NeighbourPeakIntegrator']:
		i = 0
		for event in gamma.source:
			i += 1
			if not event.r0.event_id in event_IDs:
				# continue with next event
				continue
			else:
				for tel in event.r0.tels_with_data:
					camera = event.inst.subarray.tel[tel].camera

					cfg = Config()
					cfg["ChargeExtractorFactory"]["product"] = integrator
					cfg["ChargeExtractorFactory"]["window_width"] = trace_width[camera.cam_id][0]
					cfg["ChargeExtractorFactory"]["window_shift"] = trace_width[camera.cam_id][1]

					event.dl1.tel[tel].reset()
					# set up calibrator.
					calibrator = CameraCalibrator(r1_product="HESSIOR1Calibrator", config=cfg)
					calibrator.calibrate(event)


					#####################################
					# Tino's solution for gain selection
					if (camera.cam_id == np.array(list(pe_thresh.keys()))).any():
						image = event.dl1.tel[tel].image
						image = pick_gain_channel(image, camera.cam_id, pe_thresh)
					else:
						image = event.dl1.tel[tel].image
						image = np.reshape(image[0], np.shape(image)[1])

					# image = np.reshape(image[0], np.shape(image)[1])


					EventID = [int(event.r0.event_id)] * len(image)
					TelescopeID = [int(tel)] * len(image)
					cameras = [event.inst.subarray.tel[tel].camera.cam_id] * len(image)
					PixelID = np.arange(len(image))
					charge = image
					new_df = pd.DataFrame(np.transpose([EventID, TelescopeID,
						PixelID, charge, cameras]), columns=["EventID", "TelescopeID",
						"PixelID", "charge", "cameras"])

					try:
						ctapipe_charge = ctapipe_charge.append(new_df, ignore_index=True)
					except (TypeError, NameError):
						ctapipe_charge = new_df

				print("{:.2f}% finished".format((i / len(event_IDs)) * 100))

	ctapipe_charge.to_csv('ctapipe_charge.csv', sep=",")
	return ctapipe_charge


def print_stat_error(bins, value, color=None, alpha=1):
    #error = np.sqrt(a)
    #error[~np.isfinite(err)] = 0
    #position = np.mean([b[:-1],b[1:]], axis=0)
    #plt.errorbar(position, value, yerr=error, fmt=' ', linewidth=linewidth, color=color, capsize=7, capthick=2)
    
    value = np.append(value, value[-1])
    error = np.sqrt(value)
    plt.fill_between(x=bins, y1=value+error, y2=value-error, step="post", alpha=alpha, color=color)

if __name__ == '__main__':
	print("reading ED.")
	ED_charge = read_EventDisplay("/afs/ifh.de/user/e/epuesche/scratch/trunk_22032018/trunk/integrated_charge_pe_run624.dat")
	event_IDs = np.unique(ED_charge.loc[:,"EventID"])
	print("Number of {} different event IDs found for eventdisplay".format(len(event_IDs)))
	print(event_IDs)

	try:
		ctapipe_charge = pd.read_csv('ctapipe_charge.csv', sep=",", header=0, index_col=0)
	except FileNotFoundError:
		print("The file was not found. I will run the analysis to produce the "
			"file and save it for the next time.")
		ctapipe_charge = analyze_ctapipe()


	# only positive values
	ED_charge = ED_charge[ED_charge.charge > 0]
	ctapipe_charge = ctapipe_charge[ctapipe_charge.charge > 0]

	golbal_max = np.log10(np.max([np.max(ED_charge.charge), np.max(ctapipe_charge.charge)]))
	golbal_min = np.log10(np.min([np.min(ED_charge.charge), np.min(ctapipe_charge.charge)]))

	range_hist = [-1, 4]
	nbins = 50 

	alpha = 0.4

	#binwidth = (golbal_max - golbal_min) / nbins
	#bins = np.arange(golbal_max, golbal_min + binwidth, binwidth)

	# number of charges for all telescopes
	fig = plt.figure(figsize=[7,6])
	ax = fig.add_subplot(111)
	n, bins, p = ax.hist(np.log10(ED_charge.charge), range=range_hist, bins=nbins, log=True, color="C1",
		histtype="step", label="EventDisplay", linewidth=2)
	print_stat_error(bins, n, color="C1", alpha=alpha)
	n, bins, p = ax.hist(np.log10(ctapipe_charge.charge), range=range_hist, bins=nbins, log=True, color="C0",
		histtype="step", label="ctapipe", linewidth=2)
	print_stat_error(bins, n, color="C0", alpha=alpha)

	ax.set_xlabel("log(charge) / phe", fontsize=16)
	ax.set_ylabel("Number of pixels", fontsize=16)
	plt.xlim(range_hist)
	plt.legend(fontsize=16)
	plt.title("All cameras", fontsize=16)
	plt.tight_layout()
	plt.savefig("Charge_Comparison/charges_all_cams.pdf")
	plt.close()

	# unique cameras:
	cameras = np.unique(ctapipe_charge.cameras)

	for cam in cameras:
		# get entries for this camera
		ctapipe_cam = ctapipe_charge[ctapipe_charge.cameras==cam]
		# telescope ids
		telid_cam = np.unique(ctapipe_charge.TelescopeID[ctapipe_charge.cameras==cam])
		ED_cam = ED_charge[ED_charge.TelescopeID.isin(telid_cam)]


		# number of charges for all telescopes
		fig = plt.figure(figsize=[7,6])
		ax = fig.add_subplot(111)
		n, bins, p = ax.hist(np.log10(ED_cam.charge), range=range_hist, bins=nbins, log=True, color="C1",
			histtype="step", label="EventDisplay", linewidth=2)
		print_stat_error(bins, n, color="C1", alpha=alpha)
		n, bins, p = ax.hist(np.log10(ctapipe_cam.charge), range=range_hist, bins=nbins, log=True, color="C0",
			histtype="step", label="ctapipe", linewidth=2)
		print_stat_error(bins, n, color="C0", alpha=alpha)

		ax.set_xlabel("log(charge) / phe", fontsize=16)
		ax.set_ylabel("Number of pixels", fontsize=16)
		plt.xlim(range_hist)
		plt.legend(fontsize=16)
		plt.title("{}".format(cam), fontsize=16)
		plt.tight_layout()
		plt.savefig("Charge_Comparison/charges_cam_{}.pdf".format(cam))
		plt.close()













