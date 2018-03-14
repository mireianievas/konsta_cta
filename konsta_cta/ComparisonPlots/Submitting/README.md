# Submitting multiple files for analyzing

The following scripts are primarily written in order to create comparison plots for ctapipe. Therefore, several some lines are specially added to easily extract the information needed. However, for a general analysis, they might not be interesting and should be removed. So far only low-level analysis up to image cleaning and parametrization is performed.\\
For the plots, only gamma and NSB simulations are interesting and are used for the analysis. The list of files to analyze should be contained in a list file which is passed to `submit_file.py` using the `--listGAMMA` and `--listNSB` options. An easy script to generate a list with a given number of files is given by `generate_list.sh`

If the files actually should be analyzed using the `--submit true` option. The files can either be analyzed locally or use qsub `--qsub true`. __Cautions:__ if `--submit true` and `--qsub false`, then all files will be analyzed locally simultaneously which might spam your CPU. By now the analyzed events are not written but only the numbers required for the plots are stored in one file for each run. These files are written to the directory specified with `--odir`. Log files are written to the same folder. To merge those outputs to one single file rerun `submit_file.py` without submitting using `--concatenate true`. If files aren't processed properly and the expected files aren't in `odir` it might be wanted to just take all files that were created setting `ignore_missing_files = True`

## Submission process
1. `run_analysis.sh`  
   script to just execute run_analysis.py
2. `run_analysis.py`  
   reads the file lists and arguments passed and setups output directory for each file individually. Afterwards it calls either `local_analyse_file.sh` or `qsub_analyse_file.sh` depending on `--qsub`
3. `local_analyse_file.sh` or `qsub_analyse_file.sh`  
   Setting the right version of python to use and passing submission options before calling `one_file.py`.  
    __Important:__ the maximum memory usage of this job given by `-l h_rss=8G` needs to be sufficient large because otherwise a `SIGTERM` signal is sent to cancel the job. 
4. `one_file.py`  
   read the simtel file and loop through all events applying image cleaning and write down the desired values and save them to the output directory