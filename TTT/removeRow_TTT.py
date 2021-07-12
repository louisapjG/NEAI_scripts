import csv
import numpy as np

input_file = "1_col_3d.csv"
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
	dataset, headers = intake(input_file,value_delimiter,has_header,has_index)

	#Remove first row
	mod_dataset = dataset[1:]
	#Remove first 3 row
	mod_dataset = dataset[3:]
	#Remove last 3 row
	mod_dataset = dataset[:-3]
	#Remove last column for 3d arrays
	mod_dataset = dataset[:,:-1]
	#Select 1 out 3 points 
	mod_dataset = dataset[::3]

if __name__ == "__main__":
	main(input_file,value_delimiter,has_header,has_index)