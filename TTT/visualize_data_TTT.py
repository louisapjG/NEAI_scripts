#Show data in graph format with one subplot per axis
import csv
import matplotlib.pyplot as plt

input_file = "1_col_3d.csv"
value_delimiter = ','
has_header = False
has_index = False
save_to = "test.jpeg"


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

#Display the data with one graph per column
def multi_plots(dataset,headers,save_to=""):
	plt.figure()
	if len(headers) <= 1:
		plt.title(headers[0])
		plt.plot(dataset)
	for nbr,subplot_name in enumerate(headers):
		sub_id = int(str(len(headers))+'1'+str(nbr+1))
		plt.subplot(sub_id)
		plt.title(subplot_name)
		plt.plot(dataset[:][nbr])
	
	if save_to != "":
		plt.savefig(save_to)
	plt.show()


def main(input_file,value_delimiter,has_header,has_index,save_to=""):
	dataset, headers = intake(input_file,value_delimiter,has_header,has_index)
	multi_plots(dataset,headers,save_to)

if __name__ == "__main__":
	main(input_file,value_delimiter,has_header,has_index,save_to)
