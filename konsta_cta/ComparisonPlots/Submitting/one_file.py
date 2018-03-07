import argparse
import os

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
	parser.add_argument("--run", type=int, default="",
					help="number of file")
	parser.add_argument("--dataType", type=str, default=".",
					help="dataType")
	
	args = parser.parse_args()
	file = args.file
	dataType = args.dataType
	run = args.run
	odir = args.odir

    particle.read_files(file)
    images = ImagePreparer([particle])
    images.prepare()

	# keys for particle and event_id
	keys = np.array(list(images.mc_energy.keys()))

	# empty DF to fill with number of images
	number_images = pd.DataFrame(columns=["Emc", "all_images", "cleaned"])

	for i in range(len(keys)):
		new_entry = pd.DataFrame([[
			float(images.mc_energy[keys[i, 0], int(keys[i, 1])].base),
			float(images.n_images[keys[i, 0], int(keys[i, 1])]),
			float(images.n_clean_images[keys[i, 0], int(keys[i, 1])])
		]], columns=["Emc", "all_images", "cleaned"])
		number_images = number_images.append(
			new_entry, ignore_index=True)

	output_directory = "{}/{}".format(odir, dataType)
	# creat output folder if not existing
	os.system("mkdir .p {}".format(output_directory))

	# Save the output to HDF5 file
	store = pd.HDFStore('{}/image_numbers_{}_run{}.h5'
		.format(output_directory, dataType, run))

	# save the DataFrame
	store['number_images'] = number_images