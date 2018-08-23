from ctapipe.calib.camera import CameraCalibrator  # calibration
from ctapipe.reco.HillasReconstructor import \
    HillasReconstructor, TooFewTelescopesException  # direction reconstruction
from ctapipe.calib.camera.gainselection import pick_gain_channel
from ctapipe.image.cleaning import tailcuts_clean  # image cleaning
from ctapipe.image import hillas_parameters  # hillas parametrization
from ctapipe.utils import linalg
from traitlets.config import Config  # configuration handeling
from konsta_cta.cutter import *  # apply quality cuts
from konsta_cta.reco.direction_LUT import *


class PrepareList(Cutter):
    '''
    Prepare a feature list to save to table. It takes an event, does the
    calibration, image cleaning, parametrization and reconstruction.
    From this some basic features will be extracted and written to the file
    which later on can be used for training of the classifiers or energy
    regressors.

    test
    '''

    true_az = {}
    true_alt = {}

    max_signal = {}
    tot_signal = 0
    impact = {}

    def __init__(self, event, telescope_list, camera_types, ChargeExtration,
                 pe_thresh, tail_thresholds, DirReco, quality_cuts, LUT=None):
        super().__init__()
        '''
        Parmeters
        ---------
        event : ctapipe event container
        calibrator : ctapipe camera calibrator
        reconstructor : ctapipe hillas reconstructor
        telescope_list : list with telescope configuration or "all"
        pe_thresh : dict with thresholds for gain selection
        tail_thresholds : dict with thresholds for image cleaning
        quality_cuts : dict containing quality cuts
        canera_types : list with camera types to analyze
        '''
        self.event = event
        self.telescope_list = telescope_list
        self.pe_thresh = pe_thresh
        self.tail_thresholds = tail_thresholds
        self.quality_cuts = quality_cuts
        self.camera_types = camera_types
        self.dirreco = DirReco
        self.LUTgenerator = LUT

        if (self.dirreco["weights"] == "LUT") | (self.dirreco["weights"] == "doublepass"):
            self.weights = {}
        else:
            self.weights = None

        self.hillas_dict = {}
        self.camera_dict = {}
        self.edge_pixels = {}

        # configurations for calibrator
        cfg = Config()
        cfg["ChargeExtractorFactory"]["product"] = \
            ChargeExtration["ChargeExtractorProduct"]
        cfg['WaveformCleanerFactory']['product'] = \
            ChargeExtration["WaveformCleanerProduct"]

        self.calibrator = CameraCalibrator(
            r1_product="HESSIOR1Calibrator", config=cfg)  # calibration

        self.reconstructor = HillasReconstructor()  # direction

    def get_impact(self, hillas_dict):
        '''
        calculate impact parameters for all telescopes that were
        used for parametrization.

        Paremeters
        ----------
        hillas_dict : dict with hillas HillasParameterContainers

        Returnes
        --------
        impact : impact parameter or NaN if calculation failed
        '''

        # check if event was prepared before
        try:
            assert self.reco_result
        except AssertionError:
            self.prepare()

        impact = {}
        for tel_id in hillas_dict.keys():
            try:
                pred_core = np.array([self.reco_result.core_x.value,
                                      self.reco_result.core_y.value]) * u.m
                # tel_coords start at 0 instead of 1...
                tel_position = np.array([self.event.inst.subarray.tel_coords[tel_id - 1].x.value,
                                         self.event.inst.subarray.tel_coords[tel_id - 1].y.value]) * u.m
                impact[tel_id] = linalg.length(pred_core - tel_position)
            except AttributeError:
                impact[tel_id] = np.nan

        return impact

    def get_offangle(self, tel_id):
        '''
        Get the angular offset between the reconstructed direction and the
        pointing direction of the telescope.

        Returns
        -------
        off_angles : dictionary
            dictionary with tel_ids as keys and the offangle as entries.
        '''
        off_angle = angular_separation(self.event.mc.tel[tel_id].azimuth_raw * u.rad,
                                       self.event.mc.tel[tel_id].altitude_raw * u.rad,
                                       self.reco_result.az,
                                       self.reco_result.alt)

        return off_angle

    def get_weight(self, method, camera, tel_id, hillas_par, offangle=None):
        """
        Get the weighting for HillasReconustructor. Possible methods are
        'default', which will fall back to the standard weighting applied
        in capipe, 'LUT' which will take the weights from a LUT and
        'doublepass' which might be used for diffuse simulations. In this
        case it returns the weights for the first pass.

        method : sting
            method to get the weighting.
        camera: CameraDescription
        tel_id: integer
        hillas_par: HillasParameterContainer
        """
        if method == "default":
            pass

        elif method == "LUT":
            if np.isnan(hillas_par.width) & (not np.isnan(hillas_par.length)):
                hillas_par.width = 0 * u.m

            self.weights[tel_id] = self.LUTgenerator.get_weight_from_LUT(hillas_par,
                                                                         camera.cam_id,
                                                                         min_stat=self.dirreco["min_stat"],
                                                                         ratio_cut=self.dirreco["wl_ratio_cut"][
                                                                             camera.cam_id]
                                                                         )

        elif method == "doublepass":
            # first pass with default weighting
            if np.isnan(hillas_par.width) & (not np.isnan(hillas_par.length)):
                hillas_par.width = 0 * u.m
            self.weights[tel_id] = hillas_par.intensity * (1 * u.m + hillas_par.length) / (
                    1 * u.m + hillas_par.width)

        elif method == "second_pass":
            # weights for second pass
            self.weights[tel_id] = self.LUTgenerator.get_weight_from_diffuse_LUT(self.hillas_dict[tel_id],
                                                                                 offangle, camera.cam_id,
                                                                                 min_stat=self.dirreco[
                                                                                     "min_stat"],
                                                                                 ratio_cut=
                                                                                 self.dirreco["wl_ratio_cut"][
                                                                                     camera.cam_id]
                                                                                 )

        else:
            raise KeyError("Weighting method {} not known.".format(method))

    def prepare(self):
        '''
        Prepare event performimng calibration, image cleaning,
        hillas parametrization, hillas intersection for the single
        event. Additionally, the impact distance will be calculated.
        '''

        tels_per_type = {}
        no_weight = []

        # calibrate event
        self.calibrator.calibrate(self.event)

        # loop over all telescopeswith data in it
        for tel_id in self.event.r0.tels_with_data:

            # check if telescope is selected for analysis
            # This also could be done already in event_source when reading th data
            if (tel_id in self.telescope_list) | (self.telescope_list == "all"):
                pass
            else:
                continue

            # get camera information
            camera = self.event.inst.subarray.tel[tel_id].camera
            self.camera_dict[tel_id] = camera

            image = self.event.dl1.tel[tel_id].image

            if camera.cam_id in self.pe_thresh.keys():
                image, select = pick_gain_channel(image,
                                                  self.pe_thresh[camera.cam_id], True)
            else:
                image = np.squeeze(image)

            # image cleaning
            mask = tailcuts_clean(
                camera, image,
                picture_thresh=self.tail_thresholds[camera.cam_id][1],
                boundary_thresh=self.tail_thresholds[camera.cam_id][0])

            # go to next telescope if no pixels survived cleaning
            if not any(mask):
                continue

            cleaned_image = np.copy(image)
            cleaned_image[~mask] = 0

            # calculate the hillas parameters
            hillas_par = hillas_parameters(camera, cleaned_image)

            # quality cuts
            leakage = leakage = self.leakage_cut(camera=camera, hillas_parameters=hillas_par,
                                                 radius=self.quality_cuts["leakage_cut"]["radius"],
                                                 max_dist=self.quality_cuts["leakage_cut"]["dist"],
                                                 image=cleaned_image,
                                                 rows=self.quality_cuts["leakage_cut"]["rows"],
                                                 fraction=self.quality_cuts["leakage_cut"]["frac"],
                                                 method=self.quality_cuts["leakage_cut"]["method"],
                                                 )

            size = self.size_cut(hillas_par, self.quality_cuts["size"])
            if not (leakage & size):
                # size or leakage cuts not passed
                continue

            # get the weighting for HillasReconstructor
            try:
               self.get_weight(self.dirreco["weights"], camera, tel_id, hillas_par)
            except LookupFailedError:
                # this telescope will be ignored, should only happen for method LUT here
                no_weight.append(tel_id)
                continue

            self.hillas_dict[tel_id] = hillas_par
            self.max_signal[tel_id] = np.max(cleaned_image)  # brightest pix

            try:
                tels_per_type[camera.cam_id].append(tel_id)
            except KeyError:
                tels_per_type[camera.cam_id] = [tel_id]

        try:
            assert tels_per_type
        except AssertionError:
            raise TooFewTelescopesException("No image survived the leakage "
                                            "or size cuts.")

        # wil raise exception if cut was not passed
        self.multiplicity_cut(self.quality_cuts["multiplicity"]["cuts"],
                              tels_per_type, method=self.quality_cuts["multiplicity"]["method"])

        # collect some additional information
        for tel_id in self.hillas_dict:
            self.tot_signal += self.hillas_dict[tel_id].intensity  # total size

            self.true_az[tel_id] = self.event.mc.tel[tel_id].azimuth_raw * u.rad
            self.true_alt[tel_id] = self.event.mc.tel[tel_id].altitude_raw * u.rad

        # Number of telescopes triggered per type
        self.n_tels_per_type = {tel: len(tels_per_type[tel])
                                for tel in tels_per_type}

        if self.dirreco["weights"] == "LUT":
            # remove telescopes withough weights
            print("Removed {} of {} telescopes due LUT problems".format(
                        len(no_weight), len(self.hillas_dict) + len(no_weight)))

        # do Hillas reconstruction
        self.reco_result = self.reconstructor.predict(self.hillas_dict,
                                                      self.event.inst, self.true_alt, self.true_az,
                                                      ext_weight=self.weights)

        if self.dirreco["weights"] == "doublepass":
            # take the reconstructed direction to get an estimate of the offangle and
            # get weights from the second pass from the diffuse LUT.
            self.weights = {} # reset the weights from earlier
            no_weight = []
            for tel_id in self.hillas_dict:
                offangle = self.get_offangle(tel_id)
                offangle = offangle.to(u.deg).value

                camera = self.camera_dict[tel_id] # reload camera_information

                # get the weighting for HillasReconstructor
                try:
                    self.get_weight("second_pass", camera, tel_id,
                                    self.hillas_dict[tel_id], offangle)
                except LookupFailedError:
                    no_weight.append(tel_id)

            print("Removed {} of {} telescopes due LUT problems".format(
                                    len(no_weight), len(self.hillas_dict)))

            # remove those types from tels_per_type
            for tel_id in no_weight:
                del self.hillas_dict[tel_id]
                for cam_id in tels_per_type:
                    if tel_id in tels_per_type[cam_id]:
                        index = np.where(np.array(tels_per_type[cam_id]) == tel_id)
                        tels_per_type[cam_id].pop(int(index[0]))  # remove from list

            # redo the multiplicity cut to check if it still fulfilled
            self.multiplicity_cut(self.quality_cuts["multiplicity"]["cuts"], tels_per_type,
                                  method=self.quality_cuts["multiplicity"]["method"])

            # do the second pass with new weights
            self.reco_result = self.reconstructor.predict(self.hillas_dict,
                                                          self.event.inst,
                                                          self.true_alt,
                                                          self.true_az,
                                                          ext_weight=self.weights)

        self.impact = self.get_impact(self.hillas_dict)  # impact parameter

    def get_reconstructed_parameters(self):
        '''
        Return the parameters for writing to table.

        Returns
        -------
        prepared parameters :
            impact
            max_signal
            tot_signal
            n_tels_per_type
            hillas_dict
            reco_result
        '''

        # check if event was prepared before
        try:
            assert self.impact
        except AssertionError:
            self.prepare()

        return (self.impact, self.max_signal, self.tot_signal, self.n_tels_per_type,
                self.hillas_dict, self.reco_result)
