import argparse
import os
import sys

from konsta_cta.image import ImagePreparer
from konsta_cta.readdata import FileReader

import pandas as pd
import numpy as np
#from tables import *
import pickle

if __name__ == '__main__':
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--filepath", type=str, default=None,
					help="file to process")
	parser.add_argument("--tels", type=str, default="all",
					help="file to process")
	parser.add_argument("--odir", type=str, default=".",
					help="output directory")
	parser.add_argument("--run", type=str, default="-1",
					help="number of file")
	parser.add_argument("--zenith", type=str, default="1000deg",
					help="zenith angle")
	parser.add_argument("--direction", type=str, default="1000deg",
					help="direction")
	parser.add_argument("--dataType", type=str, default=".",
					help="dataType")
	parser.add_argument("--integrator", type=str, default=None,
					help="integrator")
	parser.add_argument("--cleaner", type=str, default=None,
					help="cleaner")

	
	args = parser.parse_args()
	file = args.filepath
	dtype = args.dataType
	run = args.run
	zenith = args.zenith
	direction = args.direction
	odir = args.odir
	integrator = args.integrator
	cleaner = args.cleaner
	tels_to_use = args.tels

	
	# creat output folder if not existing
	output_directory = "{}/{}".format(odir, dtype)
	os.system("mkdir -p {}".format(output_directory))
	# delete existing output files
	os.system('rm {}/pixel_pe_{}_run{}_{}_{}.h5'.format(
			output_directory, dtype, run, integrator, cleaner))
	os.system('rm {}/image_numbers_{}_run{}_{}_{}.h5'.format(
			output_directory, dtype, run, integrator, cleaner))


	print('Reading file.\n')
	reader = FileReader(file, dtype)
	reader.read_files()
	
	print("Preparing images.\n\n")
	preparer = ImagePreparer(integrator, cleaner)
	if tels_to_use=="all":
		print("All telescopes will be considered.")
		preparer.prepare([reader])
	else:
		with open(tels_to_use) as f:
			subarray = f.read().splitlines()
		print("List of {} telescopes found for analysis:".format(len(subarray)))
		# remove white space
		subarray = [x.strip(" ") for x in subarray]
		print(subarray)
		preparer.prepare([reader], subarray=subarray)



	#####################################
	# write output for comparison plots #
	#####################################
	

	############ pixel charges ###########
	with open('{}/pixel_pe_{}_{}_{}_run{}_{}_{}.pkl'.format(
		output_directory, dtype, zenith, direction, run, integrator, cleaner), 'wb') as handle:
		pickle.dump(preparer.histograms, handle, protocol=pickle.HIGHEST_PROTOCOL)


	########## number of images ##########

	# Plots for the number of images
	# get all events
	number_images = pd.DataFrame(np.transpose([preparer.energy2, preparer.n_images,
		preparer.n_clean_images, preparer.core_x2, preparer.core_y2]),
		columns=["Emc", "all_images", "cleaned", "core_x", "core_y"])

	# Save the output to HDF5 file
	store = pd.HDFStore('{}/image_numbers_{}_{}_{}_run{}_{}_{}.h5'.format(
				output_directory, dtype, zenith, direction, run, integrator, cleaner))
	# save the DataFrame
	store['number_images'] = number_images


	############ Hillas parameters ############

	# Hillas parameters preparer
	hillas_df = pd.DataFrame(np.transpose([preparer.energy, preparer.size, preparer.length,
		preparer.width, preparer.skewness, preparer.camera, preparer.core_x,
		preparer.core_y, preparer.number_pixels]), columns=["Emc", "size", "length", "width", "skewness",
		 "camera", "core_x", "core_y", "number_pix"])
	store = pd.HDFStore('{}/hillas_{}_{}_{}_run{}_{}_{}.h5'.format(
				output_directory, dtype, zenith, direction, run, integrator, cleaner))
	# save the DataFrame
	store['hillas'] = hillas_df
	


	print("#############################")
	print("# Succefully analyzed file. #")
	print("#############################\n")
	print("Charges stored to {}/pixel_pe_{}_{}_{}_run{}_{}_{}.pkl".format(
			output_directory, dtype, zenith, direction, run, integrator, cleaner))
	print("Image numbers stored to {}/image_numbers_{}_{}_{}_run{}_{}_{}.h5".format(
				output_directory, dtype, zenith, direction, run, integrator, cleaner))
