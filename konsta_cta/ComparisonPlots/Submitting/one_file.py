import argparse
import os
import sys
import pickle

from konsta_cta.image import ImagePreparer
from konsta_cta.readdata import FileReader

import pandas as pd
import numpy as np

if __name__ == '__main__':
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--filepath", type=str, default=None,
					help="file to process")
	parser.add_argument("--odir", type=str, default=".",
					help="output directory")
	parser.add_argument("--run", type=str, default="-1",
					help="number of file")
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
	odir = args.odir
	integrator = args.integrator
	cleaner = args.cleaner

	print('Reading file.')
	reader = FileReader(file, dtype, max_events=10)
	reader.read_files()
	
	print("Preparing images.")
	preparer = ImagePreparer(integrator, cleaner)
	preparer.prepare([reader])

	#####################################
	# write output for comparison plots #
	#####################################
	
	# creat output folder if not existing
	output_directory = "{}/{}".format(odir, dtype)
	os.system("mkdir -p {}".format(output_directory))

	############ pixel charges ###########
	with open('{}/pixel_pe_{}_run{}_{}_{}.pkl'.format(
			output_directory, dtype, run, integrator, cleaner), 'wb') as f:
		pickle.dump(preparer.phe_charge, f, pickle.HIGHEST_PROTOCOL)

	########## number of images ##########
	# keys for particle and event_id
	keys = np.array(list(preparer.mc_energy.keys()))

	# Plots for the number of images
	# empty DF to fill with number of images
	number_images = pd.DataFrame(columns=["Emc", "all_images", "cleaned"])
	# get all events
	for i in range(len(keys)):
		new_entry = pd.DataFrame([[
			float(preparer.mc_energy[keys[i, 0], int(keys[i, 1])].base),
			float(preparer.n_images[keys[i, 0], int(keys[i, 1])]),
			float(preparer.n_clean_images[keys[i, 0], int(keys[i, 1])])
		]], columns=["Emc", "all_images", "cleaned"])
		number_images = number_images.append(
			new_entry, ignore_index=True)

	# Save the output to HDF5 file
	store = pd.HDFStore('{}/image_numbers_{}_run{}_{}_{}.h5'.format(
				output_directory, dtype, run, integrator, cleaner))

	# save the DataFrame
	store['number_images'] = number_images

	print("#############################")
	print("# Succefully analyzed file. #")
	print("#############################")

	print("Output stored to {}/image_numbers_{}_run{}.h5".format(output_directory, dtype, run))