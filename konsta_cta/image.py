import numpy as np

# Calibration
#############
from ctapipe.calib.camera.r1 import HESSIOR1Calibrator
from ctapipe.calib.camera.dl0 import CameraDL0Reducer
from ctapipe.calib.camera import CameraDL1Calibrator

r1cal = HESSIOR1Calibrator()
dl0cal = CameraDL0Reducer()
dl1cal = CameraDL1Calibrator()


def calibrator(event):
    r1cal.calibrate(event)
    dl0cal.reduce(event)
    dl1cal.calibrate(event)

# Image Cleaning
################
from ctapipe.image.cleaning import tailcuts_clean

# Parametrization
#################
from ctapipe.image import hillas_parameters


class ImagePreparer():
    # Class to convert Hessio raw data from r0 data level
    # to calibrated and cleaned images. Image cleaning
    # performed using tailcut cleaning.

    def __init__(self, particles=None):
        # Input
        #######
        # particles - array of konsta_cta.readdata.FileReader
        #
        self.cleaned_images = {}
        self.hillas_moments = {}
        self.n_images = {}
        self.n_images_after_cleaning = {}
        self.particles = particles
        if not self.particles:
            raise ValueError('Array of particles must be given.')
        self.keys = None
        self.geoms = self.get_all_camera_geoms()


    def analysis(self):
        # Performs the processing of the images:
        # calibration perfoming conversion from r0 to dl1
        # image cleaning using tailcut_cleaning
        # image parametrization with Hillas parameters
        #
        # Fills the dicts for cleaned_images and hillas moments

        # loop through all particle types
        for particle in self.particles:
            self.n_images[particle.datatype] = 0
            self.n_images_after_cleaning[particle.datatype] = 0

            # loop through all events
            for event in particle.source:
                # loop through all telescopes with data
                for tel_with_data in event.r0.tels_with_data:
                    self.n_images[particle.datatype] += 1
                    # calibrate data
                    calibrator(event)
                    # calibrated image
                    image = event.dl1.tel[tel_with_data].image
                    # select only the first gain and reshape array
                    image = np.reshape(image[0], np.shape(image)[1])
                    # camera geometry
                    # determine image and boundary pixels
                    mask = tailcuts_clean(
                        self.geoms[tel_with_data], image, min_number_picture_neighbors=2)

                    # drop images that didn't survive image cleaning
                    if any(mask == True):
                        self.n_images_after_cleaning[particle.datatype] += 1
                        
                        self.cleaned_images[particle.datatype,
                                            event.dl0.event_id, tel_with_data] = np.copy(image)
                        # set rejected pixels to zero
                        self.cleaned_images[particle.datatype,
                                            event.dl0.event_id, tel_with_data][~mask] = 0
                        
                        self.hillas_moments[particle.datatype, event.dl0.event_id, tel_with_data] = hillas_parameters(
                            self.geoms[tel_with_data], self.cleaned_images[particle.datatype, event.dl0.event_id, tel_with_data])

            print("Processed {} images for datatype {}. Images that didn't survive cleaning: {}".format(
                self.n_images[particle.datatype], particle.datatype, self.n_images[
                    particle.datatype] - self.n_images_after_cleaning[particle.datatype]))
        self.get_keys()

    def get_keys(self):
        # returns an numpy array of the keys
        # (used later for accessing the cleaned images)
        self.keys = np.array(list(self.cleaned_images.keys()))

    def get_all_camera_geoms(self):
        # returns a dict of all camera geometries
        geoms = None
        for particle in self.particles:
            # get the first event:
            for event in particle.source:
                break
            # read the camera imformations for al telescopes
            _geoms = {}
            for tel_id in event.inst.subarray.tel_id.item():
                _geoms[tel_id] = event.inst.subarray.tel[tel_id].camera

            # Test of the simulation files for all particle files use the same geometry
            if not geoms:
                geoms = _geoms
            else:
                if geoms == _geoms:
                    pass
                else:
                    raise Exception('Not same camera geometries for the files occured for: {}'.format(particle.datatype))
        return(geoms)