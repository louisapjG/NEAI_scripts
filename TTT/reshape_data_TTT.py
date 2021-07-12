import csv
import numpy as np

input_file = "1_col_3d.csv"
value_delimiter = ','
has_header = False
has_index = False

nbr_axis = 3
buffer_size = 16



#Takes in the data and returns an array containing it. Cleans up index and headers if present. 
def intake(file_in,value_delimiter,has_header,has_index):
	#Read data in
	with open(file_in) as csvfile:
		csvreader = list(csv.reader(csvfile, delimiter=value_delimiter))
		
		if has_header:
			headers = csvreader[0]
			csvreader = csvreader[1:]
		else:
			headers = [i for i in range(len(csvreader[0]))]
		
		if has_index:
			dataset = [[float(val) for val in row[1:]] for row in csvreader]
			headers = headers[1:]
		else:
			dataset = [[float(val) for val in row] for row in csvreader]

	return dataset, headers

def reformat(np_arr,nbr_axis,buffer_size):
	nbr_cols = nbr_axis

	np_arr = np_arr.flatten()
	nbr_vals = np_arr.shape[0]
	nbr_set_vals = int(nbr_vals/nbr_cols)
	
	overflow, nbr_sections = nbr_set_vals%buffer_size, nbr_set_vals//buffer_size
	
	if overflow > 0:
		np_reformatted = np.reshape(np_arr[:-overflow*nbr_cols],(nbr_sections,buffer_size*nbr_cols))
	else:
		np_reformatted = np.reshape(np_arr,(nbr_sections,buffer_size*nbr_cols))
	
	return np_reformatted

def main(input_file,value_delimiter,has_header,has_index,nbr_axis,buffer_size):
	dataset, headers = intake(input_file,value_delimiter,has_header,has_index)
	reformatted_arr = reformat(np.array(dataset),nbr_axis,buffer_size)

if __name__ == "__main__":
	main(input_file,value_delimiter,has_header,has_index,nbr_axis,buffer_size)