import numpy as np

from astropy import units as u

from .regressor_classifier_base import RegressorClassifierBase
from sklearn.ensemble import RandomForestRegressor

from collections import namedtuple

class EnergyRegressor(RegressorClassifierBase):
    """This class collects one regressor for every camera type -- given
    by `cam_id_list` -- to get an estimate for the distance of closest
    approach between the extended large hillas ellipse and the true
    direction of the event. Those can be used as weighting for the
    telescopes in the direction reconstruction.

    Parameters
    ----------
    regressor : scikit-learn regressor
        the regressor you want to use to estimate the shower energies
    cam_id_list : list of strings
        list of identifiers to differentiate the various sources of
        the images; could be the camera IDs or even telescope IDs. We
        will train one regressor for each of the identifiers.
    unit : astropy.Quantity
        scikit-learn regressors don't work with astropy unit. so, tell
        in advance in which unit we want to deal here.
    kwargs
        arguments to be passed on to the constructor of the regressors
    """

    def __init__(self, regressor=RandomForestRegressor,
                 cam_id_list="cam", unit=u.TeV, **kwargs):
        super().__init__(model=regressor, cam_id_list=cam_id_list,
                         unit=unit, **kwargs)

        DCA_features = namedtuple(
            "DCA_features", (
                "intensity",
                "length",
                "width",
                "skewness",
                "kurtosis",
                "r"
            ))

    def get_weight_from_model(self, hillas, cam_id):
        """same as `predict_dict` only that it returns a list of dictionaries
        with an estimate for the target quantity for every telescope
        type separately.
        more for testing- and performance-measuring-purpouses -- to
        see how the different telescope types behave throughout the
        energy ranges and if a better (energy-dependant) combination
        of the separate telescope-wise estimators (compared to the
        mean) can be achieved.
        """

        predict_list_dict = []
        for evt in event_list:
            res_dict = {}
            for cam_id, tels in evt.items():
                t_res = self.model_dict[cam_id].predict(tels).tolist()
                res_dict[cam_id] = np.mean(t_res) * self.unit
            predict_list_dict.append(res_dict)
        return predict_list_dict

        tel_features = DCA_features(
            intensity = hillas.intensity,
            length = hillas.length,
            width = hillas.width,
            skewness = hillas.skewness,
            kurtosis = hillas.kurtosis,
            r = hillas.r
            )

        predicted_dca = self.model_dict[cam_id].predict(tel_features).tolist()
        weight = 1 / predicted_dca**2

        return weight

    @classmethod
    def load(cls, path, cam_id_list, unit=u.TeV):
        """this is only here to overwrite the unit argument with an astropy
        quantity
        Parameters
        ----------
        path : string
            the path where the pre-trained, pickled regressors are
            stored `path` is assumed to contain a `{cam_id}` keyword
            to be replaced by each camera identifier in `cam_id_list`
            (or at least a naked `{}`).
        cam_id_list : list
            list of camera identifiers like telescope ID or camera ID
            and the assumed distinguishing feature in the filenames of
            the various pickled regressors.
        unit : astropy.Quantity
            scikit-learn regressor do not work with units. so append
            this one to the predictions. assuming that the models
            where trained with consistent units. (default: u.TeV)
        Returns
        -------
        EnergyRegressor:
            a ready-to-use instance of this class to predict any
            quantity you have trained for
        """
        return super().load(path, cam_id_list, unit)