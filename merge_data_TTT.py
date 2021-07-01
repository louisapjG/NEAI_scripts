import csv
import numpy as np

input_file = ["1_col_3d.csv","1_col_3d.csv"]
value_delimiter = ','
has_header = False
has_index = False




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


def main(input_file,value_delimiter,has_header,has_index):
	dataset0, headers = intake(input_file[0],value_delimiter,has_header,has_index)
	dataset1, headers = intake(input_file[1],value_delimiter,has_header,has_index)

	datasets = [dataset0,dataset1]
	merged_datasets = np.concatenate(datasets)

if __name__ == "__main__":
	main(input_file,value_delimiter,has_header,has_index)