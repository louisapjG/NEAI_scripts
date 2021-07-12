#Inputs: CSV names, rows length, subsampling rate, train/test split ratio, output folder

# Load data in target CSV files as outputted by current Matlab script (in rows)
# Convert each import into rows of length X individually
# Split each in Train/Test sets
# Merge Trains together and Tests together
# Write to output folder 

#To take in all files in specified folders and write them in rows of 512 values at frequency of 16 for data with 2 axis
#python data_org_merge.py -b 512 -a 2 -F 16 -f KA01CSV/* KA03CSV/* KA04CSV/* KA05CSV/* KA06CSV/* KA07CSV/* KA08CSV/* KA09CSV/* KA15CSV/* KA16CSV/* KA22CSV/* -o test_outAbnormal.csv
#1 axis data
#python data_org_merge.py -b 512 -a 1 -F 16 -f KA01CSV/* KA03CSV/* KA04CSV/* KA05CSV/* KA06CSV/* KA07CSV/* KA08CSV/* KA09CSV/* KA15CSV/* KA16CSV/* KA22CSV/* -o test_outAbnormal.csv

#To Read/Write/manipulate data
import csv
import numpy as np
from scipy.io import wavfile
#To read command line arguments
from argparse import ArgumentParser
import os

LOGIC PROBLEM IN REFORMAT() the return staement returning np.array(ref_arrs)[0]. Why [0]????
 
# Reading object
# Create output file
# Check nbr axis == nbr columns
# If only one row: take it as the col
# Subsample setting (read in only selected lines)
# Split non randomly ()
# Read in X lines (nbr of values per signal)

def read_args():
	"""Read arguments from command line"""
	parser = ArgumentParser(description="NEAI Formatter")

	#Files in. For anomaly detection give nominal first and abnormal second
	parser.add_argument('-f', '--files_in', nargs='+', help="Each classe's file paths", required=True, type=str)
	
	#index
	parser.add_argument('-i', '--index', help='Call if first column is an index', dest='index', action='store_true')
	parser.set_defaults(index=False)
	
	#Header
	parser.add_argument('-H', '--header', help='Call if first row are headers', dest='header', action='store_true')
	parser.set_defaults(header=False)
	
	# Value delimiter
	parser.add_argument('-d', '--value_delimiter', help='Symbol used to seperate values in input csv file. Default: ","', required=False, default=',')
	
	# Buffer size
	parser.add_argument('-b', '--buffer_sizes', nargs='*', help='Int, multiple of 2 used to define the length of the signal used. Default 64', required=False, type=int, default=[2**x for x in range(4,15)])
	
	# train_test_split
	parser.add_argument('-s', '--split', help='Portion of data in val. If .33: 1/3 of the data will be for val and 2/3 training. If >1 nbr of signals used for testing', required=False, type=float, default=0)
	
	# Guetting Frequency for sampling
	parser.add_argument('-F', '--freq', help="input value will determin the ratio of sampling so 2 would mean we select 1 out of every 2, value 3 means 1 out of 3", required = False, type = int, default = 0)
	
	#Should Frequency data be reused 
	parser.add_argument('-R', '--freq_reuse', help='Flag to reuse data when subsampling', dest='freq_reuse', action='store_true')
	parser.set_defaults(freq_reuse=False)
	
	# Nbr of axis
	parser.add_argument('-a', '--nbr_axis', help='int input for nbr axis, by default will be set to the nbr of columns', dest='nbr_axis',type=int)
	parser.set_defaults(nbr_axis=1)

	#Output file. FULL PATH RECOMMENDED
	parser.add_argument('-o', '--output_file', help='Files will be concatenated and use this as the root of the output file', required=False, default=os.path.join(os.getcwd(),'out.csv'))

	#To append output to an existing CSV
	parser.add_argument('-A', '--append_out', help='FLAG: indicates to set the write flag to append so that instead of replacing a csv with the same name it appends data to it',dest='append_out', action='store_true')
	parser.set_defaults(append_out=False)

	return parser.parse_args()

# Read files
	#Find columns names
	#drop lines with NA
def intake(args,file_in):
	#Read data in
	with open(file_in) as csvfile:
		csvreader = csv.reader(csvfile, delimiter=args.value_delimiter)
		if args.header:
			csvreader = csvreader[1:]
		if args.index:
			dataset = [row[1:] for row in csvreader]
		else:
			dataset = [row for row in csvreader]


	return dataset

def intake_wav(args, file_in):
	nom_samplerate, nom_data = wavfile.read(file_in)

	if args.index:
		nom_data = nom_data.drop(nom_data.columns[0], axis=1)

	return nom_data

#Check for input shape (in case we have everything in one row)
#return numpy arr
def shape_check(args, data):
	#Need tto reshape row to column
	if len(data) <= args.nbr_axis:
		data = np.array(data).T
	else:
		data = np.array(data)

	return data

#Check the we have enough continuous data point for the line length * subsampling
def reformating_sanity_check(args, np_arr, buffer_size, file_in):
	nbr_rows = np_arr.shape[0]
	if args.freq != 0:
		base_nbr_continuous_signal = buffer_size*args.freq
		if nbr_rows < base_nbr_continuous_signal:
			print("1 row of data with a freq of ",args.freq," and buffer len of ", buffer_size, " requires at least ",base_nbr_continuous_signal," rows of data, every additional row requires ",buffer_size, " data points")
			print("Current number of rows: ",nbr_rows)
			print("FileName:",file_in)
			quit()

#Return arr of arrays each an iteration of the subsampling. Only one array in array if reuse is false. 
def subsample(args, np_arr):
	if args.freq == 0: return np_arr

	#simulate a one axis array
	ind = np.array([a for a in range(int(len(np_arr)/args.nbr_axis))])
	
	#Select proper frequency/ies from that one axis array
	if args.freq_reuse:
		inds = [ind[start::args.freq] for start in range(args.freq)]
	#Take every value and only keep 1/freq
	else:
		inds = [ind[::args.freq]]

	#Re-expand to proper nbr of axis
	selections = []
	for ind in inds:
		sel = []
		for val in ind:
			for a in range(args.nbr_axis):
				sel.append(np_arr[val+a])

		selections.append(np.array(sel))

	return selections


	
	# if args.freq_reuse:
	# 	np_arrs = [np_arr[start::args.freq, :] for start in range(args.freq)]
	
	# #Take every value and only keep 1/freq
	# else:
	# 	np_arrs = [np_arr[::args.freq, :]]

	#return np_arrs

#Takes in array of array. Reformat internal arrays and stitch them together
def reformat(args,np_arrs,buffer_size):
	ref_arrs = []
	nbr_cols = args.nbr_axis

	for np_arr in np_arrs:
		np_arr = np_arr.flatten()
		nbr_vals = np_arr.shape[0]
		nbr_set_vals = int(nbr_vals/nbr_cols)
		
		overflow, nbr_sections = nbr_set_vals%buffer_size, nbr_set_vals//buffer_size
		
		if overflow > 0:
			np_reformatted = np.reshape(np_arr[:-overflow*nbr_cols],(nbr_sections,buffer_size*nbr_cols))
		else:
			np_reformatted = np.reshape(np_arr,(nbr_sections,buffer_size*nbr_cols))
		
		ref_arrs.append(np_reformatted)

	return np.array(ref_arrs)[0]

#Split dataset in random train/test splits
def split_arr(args,np_arr):
	nbr_vals = int(args.split*len(np_arr))
	all_ind = [a for a in range(len(np_arr))]
	val_ind = np.random.choice(all_ind,size=nbr_vals,replace=False).astype(int)
	train_ind = np.delete(all_ind,val_ind).astype(int)#np.in1d(all_ind,val_ind,invert=True)

	return np_arr[train_ind], np_arr[val_ind]

#Generate output file name
def name_out_file(output_file, buffer_size, train_val='train', freq=0):
	return os.path.splitext(output_file)[0]+'_'+train_val+'_'+str(buffer_size)+'_F_'+str(freq)+'.csv'

def write_csv(output_file_name,arr):
	with open(output_file_name, 'w') as csvfile:
		csv_writer = csv.writer(csvfile)
		for row in arr:
			csv_writer.writerow(row)

def main():
	#Grab command from cli
	args = read_args()

	nbr_files = len(args.files_in)

	#For all buffer sizes specified
	for buffer_size in args.buffer_sizes:
		dfs = {'train':[],'val':[]}
		#For each files fed in
		for file_in in args.files_in:
			
			#Read in file
			if os.path.splitext(file_in)[1] == ".wav":
				data = intake_wav(args, file_in)
			else:
				data = intake(args, file_in)

			#reshape if input is one row
			np_arr = shape_check(args,data)

			#Check if the number of data points allows for the line length * subsampling
			reformating_sanity_check(args, np_arr, buffer_size, file_in)

			#Subsample data
			np_arrs = subsample(args, np_arr)

			#Organize data in proper line length
			np_arr_reformatted = reformat(args,np_arrs,buffer_size)

			#Split
			if args.split > 0:
				arr_train, arr_val = split_arr(args,np_arr_reformatted)
				dfs['val'].append(arr_val)
				dfs['train'].append(arr_train)
			else:
				dfs['train'].append(np_arr_reformatted)


		#Merge & write out
		train = np.concatenate(dfs['train'])
		write_csv(name_out_file(args.output_file, buffer_size, train_val='train', freq=args.freq),train)
		if args.split > 0:
			val = np.concatenate(dfs['val'])
			write_csv(name_out_file(args.output_file, buffer_size, train_val='validation', freq=args.freq),val)


if __name__ == "__main__":
	main()

