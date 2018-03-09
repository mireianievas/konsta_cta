import os
import pandas as pd
import argparse

from plot_numTELSvsENERGY import plot_numTELSvsENERGY

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("--datadir", type=str, default="./Analysis",
						help="maximum number of events per file")
	parser.add_argument("--odir", type=str, default="./Plots",
						help="maximum number of events per file")
	parser.add_argument("--numTELS_ENERGY", type=bool, default=False,
						help="Plot number of telescopes with image"
						"after cleaning vs energy")

	args = parser.parse_args()

	odir = args.odir
	# creat ouput directory
	os.system("mkdir -p {}".format(odir))
	datadir = args.datadir


	# open the outputs from the submited processes.
	try:
		store_gamma = pd.HDFStore("{}/gamma/image_numbers_gamma_allruns.h5"
			.format(datadir))
		# read Dataframes
		images_gamma = store_gamma['number_images']
	except:
		print("No file found for gamma. Did you run submit_file.py"
			" with option concatenate before?")

	try:
		store_gamma = pd.HDFStore("{}/NSB/image_numbers_NSB_allruns.h5"
			.format(datadir))
		# read Dataframe
		images_nsb = store_nsb['number_images']
	except:
		print("No file found for NSB. Did you run submit_file.py"
			" with option concatenate before?")
 
	# generate plots
	if (args.numTELS_ENERGY):
		plot_numTELSvsENERGY(images_gamma, "{}/imagevsenergy"
			"_{}events".format(odir, len(images_gamma)))
