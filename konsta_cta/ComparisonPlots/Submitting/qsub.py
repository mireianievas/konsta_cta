import subprocess
import shlex

import pandas as pd
import argparse

if __name__ == '__main__':
	parser.add_argument("--listGAMMA", type=str, default=None,
						help="list of gamma files")
	parser.add_argument("--listNSB", type=str, default=None,
						help="list of NSB files")
	parser.add_argument("--submit", type=bool, default=False,
						help="submit the jobs")
	parser.add_argument("--concatenate", type=bool, default=False,
						help="concatenate all outputs")
	parser.add_argument("--odir", type=str, default=".",
						help="output directory")

	args = parser.parse_args()

	odir = args.odir
	
	if args.submit & args.concatenate:
		raise ValueError("submit and concatenate not executable at same time")

	lists = []
	dtypes = []
	for arg, dtype in zip([args.listGAMMA, args.listNSB],["gamma, NSB"]):
		if arg:
			lists.append(arg)
			dtypes.append(dtype)
			print("list of {} files added.".format(args.listGAMMA))

	for file_list, dtype in zip(lists, dtypes):
		if args.concatenate:
			# generate empty DataFrame
			number_images = pd.DataFrame(columns=["Emc", "all_images", "cleaned"])
		# read the list of files
		files = open(file_list).readlines()
		
		# iterate each of the files	    
	    for file in files:
	    	# get runnumber
	    	substr = file[file.find("run")+3:file.find("_cta")]
			runnumber = [int(s) for s in substr.split("_") if s.isdigit()][0]

			if args.submit:
				# create folder for the log files
				log_dir = "{}/LOGS".format(odir)
				log_name = "{}/{}_{}".format(log_dir, dtype, runnumber)

				os.system("mkdir -p {}".format(log_dir))
				# submit sh file that to submit ""
				subprocess.call("qsub -l h_rt=18:00:00 -l h_rss=4G -o {}_output.txt -e {}_errors.txt ./source_analysis.sh {} {} {} {}".format(log_name, log_name, file, runnumber, dtype, odir))
		        





		    if args.concatenate:
				# get stored dataframes
				store = pd.HDFStore('image_numbers_{}_run{}.h5'
					.format(dtype, runnumber))
				_number_images = store['number_images']
				# append all files to one DF
				number_images = number_images.append(_number_images)

		if args.concatenate:
			store = pd.HDFStore('image_numbers_{}_allruns.h5'
					.format(dtype))
			# Save the output to HDF5 file
			store['number_images'] = number_images