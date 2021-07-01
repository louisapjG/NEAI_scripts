#Show data in graph format with one subplot per axis
import csv
import matplotlib.pyplot as plt

input_file = 
value_delimiter = ','
has_header = True
has_index = True
save_to = ""

def intake(file_in,value_delimiter,has_header,has_index):
	#Read data in
	with open(file_in) as csvfile:
		csvreader = csv.reader(csvfile, delimiter=value_delimiter)
		
		if has_header:
			headers = csvreader[0]
			csvreader = csvreader[1:]
		else:
			headers = [i for i in range(len(csvreader[0]))]
		
		if has_index:
			dataset = [row[1:] for row in csvreader]
			headers = headers[1:]
		else:
			dataset = [row for row in csvreader]


	return dataset, headers

def multi_plots(dataset,headers,save_to=""):
	plt.figure()
	for nbr,subplot_name in enumerate(headers):
		sub_id = int(str(len(headers))+'1'+str(nbr+1))
		plt.subplot(sub_id)
		plt.title(subplot_name)
		plt.plot(dataset[:,nbr])
	
	if save_to != "":
		plt.savefig(save_to)
	plt.show()


def main(input_file,value_delimiter,has_header,has_index):
	dataset, headers = intake(input_file,value_delimiter,has_header,has_index)
	multi_plots(dataset,headers,)

if __name__ == "__main__":
	main()
