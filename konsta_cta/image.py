import warnings
import numpy as np

# Calibration
#############
from ctapipe.calib.camera import CameraCalibrator

# Image Cleaning
################
from ctapipe.image.cleaning import tailcuts_clean

# Parametrization
#################
from ctapipe.image import hillas_parameters

import sys

class ImagePreparer():
    ''' Class to convert Hessio raw data from r0 data level
        to calibrated and cleaned images. Image cleaning
        performed using tailcut cleaning.
    
    '''

    # for storing data
    clean_images = {}
    hillas_moments = {}
    sum_images = {}
    sum_clean_images = {}
    mc_image = {}
    mc_energy = {}
    n_clean_images = {}
    n_images = {}

    phe_charge = {}


    ## QUESTION: what values for other cameras??
    # from Tino
    pe_thresh = {
        "ASTRICam": 14,
        "LSTCam": 100,
        "NectarCam": 190}

    # for analysing HESSIO file
    r1 = "HESSIOR1Calibrator"

    def __init__(self, integrator=None, cleaner=None):
        self.keys = None
        self.integrator = integrator
        self.cleaner = cleaner
        

    def prepare(self, particles, hillas=False):
        ''' Performs the processing of the images:
            calibration perfoming conversion from r0 to dl1
            image cleaning using tailcut_cleaning
            image parametrization with Hillas parameters
            
            Fills the dicts for clean_images and hillas moments
        '''
        # Input
        #######
        # particles - array of konsta_cta.readdata.FileReader
        #

        self.particles = particles
        self.geoms, self.geoms_unique = self.get_camera_geoms()

        # loop through all particle types
        for particle in self.particles:
            dtype = particle.datatype

            # count number of images and number after cleaning
            self.sum_images[dtype] = 0
            self.sum_clean_images[dtype] = 0

            # set up calibrator
            calibrator = CameraCalibrator(r1_product=self.r1,
                        integrator=self.integrator, cleaner=self.cleaner)
            
            # loop through all events
            for event in particle.source:
                
                event_id = event.dl0.event_id
                n_images = 0
                n_clean_images = 0
                self.mc_energy[dtype, event_id] = event.mc.energy
                # loop through all telescopes with data
                for tel_id in event.r0.tels_with_data:
                    n_images += 1

                    # get camera information
                    camera = event.inst.subarray.tel[tel_id].camera

                    # mc Image (why are they empty???)
                    self.mc_image[dtype, event_id, tel_id] = event.mc.tel[tel_id].photo_electron_image
                    
                    # calibrate event
                    calibrator.calibrate(event)

                    ######################################
                    # create output for comparison plots #
                    ######################################

                    # charge of each pixel in pe

                    cam_id = camera.cam_id

                    number_gains = event.dl1.tel[tel_id].image.shape[0]
                    for gain in range(number_gains):
                        try:
                            self.phe_charge[cam_id,gain].extend(list(event.dl1.tel[tel_id].image[gain]))
                        except:
                            self.phe_charge[cam_id,gain] = list(event.dl1.tel[tel_id].image[gain])

                    #####################################
                    # Tino's solution for gain selection
                    if (camera.cam_id == np.array(list(self.pe_thresh.keys()))).any():
                        image = event.dl1.tel[tel_id].image
                        image = self.pick_gain_channel(image, camera.cam_id)
                    else:
                        image = event.dl1.tel[tel_id].image
                        image = np.reshape(image[0], np.shape(image)[1])

                    ######################
                    # image cleaning
                    mask = tailcuts_clean(
                        self.geoms[tel_id], image,
                        min_number_picture_neighbors=2
                        )

                    # drop images that didn't survive image cleaning
                    if any(mask == True):
                        n_clean_images += 1
                        self.clean_images[dtype, event_id, tel_id] = np.copy(image)
                        # set rejected pixels to zero
                        self.clean_images[dtype, event_id, tel_id][~mask] = 0

                        if hillas:
                            self.hillas_moments[dtype, event_id, tel_id] = hillas_parameters(
                                self.geoms[tel_id], self.clean_images[dtype, event_id, tel_id], True)
                        else:
                            pass

                # count number of images at trigge level and after cleaning
                # summary:
                self.sum_images[dtype] += n_images
                self.sum_clean_images[dtype] += n_clean_images
                # per event:
                self.n_clean_images[dtype, event_id] = n_clean_images
                self.n_images[dtype, event_id] = n_images

            print("Processed {} images for datatype {}. Images " 
                   "that didn't survive cleaning: {}".format(
                    self.sum_images[dtype], dtype,
                    self.sum_images[dtype] - self.sum_clean_images[dtype])
                  )
        self.get_keys()


    def get_keys(self):
        # returns numpy array of the keys
        self.keys = np.array(list(self.clean_images.keys()))
        self.keys2 = np.array(list(self.n_clean_images.keys()))

    def get_camera_geoms(self):
        # returns dict of all camera geometries
        geoms = None
        for particle in self.particles:
            # get the first event:
            for event in particle.source:
                break

            # read the camera imformations for al telescopes
            _geoms = {}
            for tel_id in event.inst.subarray.tel_id.item():
                _geoms[tel_id] = event.inst.subarray.tel[tel_id].camera

            # Check geometry for all particle files 
            if not geoms:
                geoms = _geoms
            else:
                if geoms == _geoms:
                    pass
                else:
                    warnings.warn('Not same camera geometries for the files'
                        'occured for: {}'.format(particle.datatype))

            geoms_unique = []
            for geo in geoms:
                try:
                    if not any(geoms[geo].cam_id == np.array(geoms_unique)):
                        geoms_unique.append(geoms[geo].cam_id)
                except:
                    if len(geoms_unique)==0:
                        geoms_unique.append(geoms[geo].cam_id)
                    
        return(geoms, geoms_unique)

    def pick_gain_channel(self, pmt_signal, cam_id):
        '''the PMTs on some (most?) cameras have 2 gain channels. select one
        according to a threshold. ultimately, this will be done IN the
        camera/telescope itself but until then, do it here
        '''
        np_true_false = np.array([[True], [False]])
        if pmt_signal.shape[0] > 1:
            pmt_signal = np.squeeze(pmt_signal)
            pick = (self.pe_thresh[cam_id] <
                    pmt_signal).any(axis=0) != np_true_false
            pmt_signal = pmt_signal.T[pick.T]
        else:
            pmt_signal = np.squeeze(pmt_signal)
        return pmt_signal

