# write feature list

Scripts for generating a feature list for training of the models for gamma hadron seperation and the energy reconstruction.

The low level reconstruction up to the direction reconstruction is performed and the important feaures can be written to the feature list. The scripts are written for submitting the jobs to the DESY batch farm. To submit a list of runs use submit.py. Besides runlist(s) the script can take a directory to write the output in as well as the path to a list of telescopes to use in the analysis. The configurations for the analysis are passed in a .json file. The log files will be written to the same directory as the output.


The mode to run the script will be passed in this configuration file. Possible modes are 
- `make_direction_LUT`: Will create a look up table for each file in the runlist, storing the estemating DCA values in dependency of size and the ratio of width / length. Options for the binning also are passed in the config file. The DCA might be used for the weighting of the `HillasPlanes` in the `HillasReconstructor`.
- `merge_LUT`: Merge the LUT written in `odir` to one look up table. It requires that the binning in each of the LUTs are equal. The merged LUT will be written to `ctapipe_aux_dir`
- `write_list_dca`: Create a list for each telescope type containing the DCA value for each telescope as well as size, length, width, skewness, kurtosis which might be used for training a RF to estimate the dca.
- `write_lists`: Write a feature list with parameters for the training of the models. The weighting method as well as further parameters are given in the configuration file.

### qsub_file
Set the correct environment variables for the analysis, e.g. activate cta_dev and start the analysis.

### analysie_file_write_list
Script to perfom the analysis per file, collect the output and write it to files.

### prepare_featurelist
The actual analysis is performed by `PrepareList`. Additionally the optional quality cuts are applied during the analysis.

### Quality cuts
Beside just performing the analysis, some basic quality cuts can be performed. Those are defined in `cutter.py`.  
- leakage cut: Cut on the distance of the c.o.g. to the camera center or on the fraction of charge in the boundary pixels.
- size cut: Cut on the total charge in the images
- multiplicity cut: Cut on the total number of images, or on the total number of images and the number of images per telescope type. If wanted, types not passing this cut can also be removed for the direction reconstruction.

### direction LUT
A class to create a LUT for the DCA values per telescope type is defined in `direction_LUT.py`. It is based on the basic LUT handeling defined in `lookup_base.py`.