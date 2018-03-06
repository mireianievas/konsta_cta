import sys
import argparse
import pandas as pd
import numpy as np

from konsta_cta.readdata import FileReader
from konsta_cta.image import ImagePreparer

from plot_numTELSvsENERGY import plot_numTELSvsENERGY


''' Process simtel array files for cta using cta-pipe.

Generate comparison plots for ctapipe.


input:
------
--pathGAMMA 	Path to gamma files
--pathPROTON 	Path to proton files
--list		NOT PROPERLY SUPPORTED SO FAR --> readdata.py

#########
To do:
- adapt it for parallel computing using qsub

set up reader
for each file for particle:
	qsub to calibrate and clean images
	write needed output to file

external script:
read output and combine it to generate plots
'''

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument("--maxEVENTS", type=int, default=None,
						help="maximum number of events per file")
	parser.add_argument("--pathGAMMA", type=str, default=None,
						help="Path to gamma files")
	parser.add_argument("--pathNSB", type=str, default=None,
						help="Path to proton files")
	parser.add_argument("--listGAMMA", type=str, default=None,
						help="list of gamma files")
	parser.add_argument("--listNSB", type=str, default=None,
						help="list of proton files")
	parser.add_argument("--numTELS_ENERGY", type=bool, default=False,
						help="Plot number of telescopes with image"
						"after cleaning vs energy")
	parser.add_argument("--prepare", type=bool, default=False,
						help="if True perform calibration and cleaning")

	args = parser.parse_args()

	list_gammas = args.listGAMMA
	list_NSB = args.listNSB
	path_gammas = args.pathGAMMA
	path_NSB = args.pathNSB

	# collect list of particles
	particles = []
	try:
		print("---------reading Gamma---------")
		gamma = FileReader(list_gammas, "Gamma", args.maxEVENTS)
		particles.append(gamma)
	except ValueError:
		print('Now trying gnereate list from path.')
		try:
			gamma = FileReader.get_file_list(path_gammas,
											 "Gamma", args.maxEVENTS)
			particles.append(gamma)
		except IOError:
			print('No path given for gammas.')
			if args.numTELS_ENERGY:
				sys.exit("Gamma data needed for numTELS_ENERGY")
		except ValueError:
			print("List is empty.")
			if args.numTELS_ENERGY:
				sys.exit("Gamma data needed for numTELS_ENERGY")

	try:
		print("----------reading NSB----------")
		NSB = FileReader(list_NSB, "NSB", args.maxEVENTS)
		particles.append(NSB)
	except ValueError:
		print('Now trying gnereate list from path.')
		try:
			NSB = FileReader.get_file_list(path_NSB, "NSB", args.maxEVENTS)
			particles.append(NSB)
		except IOError:
			print('No path given for NSB.')
		except ValueError:
			print("List is empty.")

	for particle in particles:
		print("-------------------------------")
		print("Number of files for {}: {}"
			  .format(particle.datatype, len(particle.file_list)))

	number_images = pd.DataFrame(columns=["Emc", "all_images", "cleaned"])
	
	# Save the output to HDF5 file
	store = pd.HDFStore('images.h5')
	
	if args.prepare:
		# particle types
		for particle in particles:
			print("--------starting with {}--------".format(particle.datatype))
			# set up generator for reading files:
			generator = particle.files_as_generator()
			# all files
			for i in range(len(particle.file_list)):
				# reed next file
				print("-----------next file-----------")
				next(generator)

				# prepare the image
				images = ImagePreparer([particle])
				images.analysis(hillas=False)

				if (args.numTELS_ENERGY) & (particle.datatype == 'Gamma'):

					# keys for particle and event_id
					keys = np.array(list(images.mc_energy.keys()))

					for i in range(len(keys)):
						new_entry = pd.DataFrame([[
							float(images.mc_energy[keys[i, 0], int(keys[i, 1])].base),
							float(images.n_images[keys[i, 0], int(keys[i, 1])]),
							float(images.n_clean_images[keys[i, 0], int(keys[i, 1])])
						]], columns=["Emc", "all_images", "cleaned"])
						number_images = number_images.append(
							new_entry, ignore_index=True)
		# save the DataFrame
		store['number_images'] = number_images

	# generate plots
	if (args.numTELS_ENERGY):
		# read DataFrame
		number_images = store['number_images']
		plot_numTELSvsENERGY(number_images, "Plots/imagevsenergy"
			"_{}events".format(len(number_images)))
