import numpy as np
from itertools import chain

class MultiplicityException(Exception):
	'''
	Exception raised if multiplicity error was not passed
	'''
	pass

class Cutter(object):
	'''
	Base class to reject objects and apply quality cuts.
	'''

	def __init__(self, quality_cuts):
		self.quality_cuts = quality_cuts

	def get_edge_pixels(self, camera, rows=1):
		'''
		Get the boundary pixels of the camera.

		Parameters
		----------
		camera : event.inst.subarray.tel camera information
		rows : number of rows considered as edge
		
		Returns
		-------
		indices of the boundary pixels of the camera
		'''

		if camera.pix_type == "hexagonal":
			expected_number_neigbours = 6
		else:
			expected_number_neigbours = 4

		number_pixels = camera.pix_id[-1] + 1

		# get the most most outer row
		N_neig = sum(camera.neighbor_matrix)
		neigh = np.arange(0, number_pixels)\
				[N_neig < expected_number_neigbours]

		for i in range(rows-1):
			#iteratively adding one line:
			neigh = np.array(camera.neighbors)[neigh]
			neigh = neigh.tolist()
			neigh = np.unique(list(chain.from_iterable(neigh)))

		return neigh
	
	def leakage_radius(self, camera, hillas_parameters,
						  radius=0.8, method="mean"):
		'''
		Handeling of images at the edge of the camera. Pictures
		with c.o.g. (hillas r) outside of radius will be rejected.

		Parameters
		----------
		camera : event.inst.subarray.tel camera information
		hillas_parameters : HillasParametersContainer
		radius : maximum relative distance of cog to center
			of the camera
		metho : ["mean", "max"]
			Method to calculate the total size of the camera

		Returns
		-------
		True if the cog is within accepted radius, otherwiese False
		'''

		# get the maximum distance from camera
		if method == "max":
			max_dist_camera = max(np.sqrt(camera.pix_x**2 + camera.pix_y**2))

		elif method == "mean":
			try:
				edge_pix = self.edge_pixels[camera.cam_id]
			except KeyError:
				edge_pix = self.get_edge_pixels(camera)
				self.edge_pixels[camera.cam_id] = edge_pix

			max_dist_camera = sum(np.sqrt(camera.pix_x**2 + \
						camera.pix_y**2)[edge_pix]) / len(edge_pix)
		else:
			raise KeyError("The method {} for calculating "
				"max_dist_camera is not known.".format(method))
		
		accepted_dist = radius * max_dist_camera

		return (hillas_parameters.r < accepted_dist)


	def leakage_fraction(self, camera, image, rows=2, fraction=0.15):
		'''
		Reject images if the fraction of charge in outer pixels
		is above the given value.
		
		Parameters
		----------
		camera : event.inst.subarray.tel camera information
		image : image in camera in pe
		rows : number of rows defining edge
		fraction : maximum fraction of charge contained
			in edge of camera

		Returns
		-------
		True if leakage cut was passed, False otherwise
		'''

		try:
			edge_pix = self.edge_pixels[camera.cam_id]
		except KeyError:
			edge_pix = self.get_edge_pixels(camera, rows)
			self.edge_pixels[camera.cam_id] = edge_pix

		# fraction of charge in edge
		frac = sum(image[edge_pix]) / sum(image)

		return frac <= fraction

	
	def size_cut(self, hillas_parameters, min_size):
		'''
		Applying size cut

		Parameters
		----------
		hillas_parameters : HillasParametersContainer
		min_size : sizevalue to cut

		Returns
		-------
		True if size cut was passed else false
		'''

		return (hillas_parameters.intensity >= min_size)


	def multiplicity_cut(self, min_multiplicity, tels_per_type=None, method="total"):
		'''
		Apply a multiplicity_cut

		Parameters
		----------
		min_multiplicity : integer or dictionary
			Minimum number of telescopes required
		tels_per_type : dictionary
			Dict containing the telescope IDs per telescope type in a
			tuple or list.

		Raises MultiplicityException if multiplicity cut was not passed
		'''

		n_tels_per_type = {tel: len(tels_per_type[tel]) for tel in tels_per_type}

		if (method == "None"):
			'''
			Skip the multiplicity cut
			'''
			reject_event = False

		elif (method == "total"):
			'''
			apply a cut on the total number of images per telescope.
			'''
			nimages = sum(n_tels_per_type.values())
			reject_event = (nimages < min_multiplicity["total"])
			

		elif (method == "per_type"):
			'''
			check total telescope numbers per telescope. keep event unless
			all telescope types do not pass the cut or the total amound of
			images is below the total required number.
			'''
			nimages = sum(n_tels_per_type.values())
			reject_total = (nimages < min_multiplicity["total"])

			limits = [min_multiplicity[tel] for tel in n_tels_per_type.keys()]
			reject_per_type = np.less(list(n_tels_per_type.values()), limits).all()

			reject_event = (reject_total or reject_per_type)


		elif (method == "per_type_remove"):
			'''
			remove telescope types that do not pass n_tels_per_type cut and
			check if total number of images that are left pass n_tels cut. 
			'''
			limits = [min_multiplicity[tel] for tel in n_tels_per_type]
			reject_per_type = np.less(list(n_tels_per_type.values()), limits)

			rejected_types = np.array(list(n_tels_per_type.keys()))[reject_per_type]

			#for tel in rejected_types:
			#	del n_tels_per_type[tel]
			#	del tels_per_type[tel]

			nimages = sum(np.array(list(n_tels_per_type.values()))[~reject_per_type])
			reject_event = (nimages < min_multiplicity["total"])

		else:
			raise KeyError("Method {} not known for multiplicity_cut.".format(method))

		if reject_event:
			raise MultiplicityException("Not enough telescopes in in event.")
		elif (method == "per_type_remove"):
			return rejected_types
		else:
			return np.array([]) # no type removed