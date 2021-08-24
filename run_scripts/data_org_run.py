from data_org_merge import read_args,intake,intake_wav,shape_check,reformating_sanity_check,subsample,reformat,split_arr,name_out_file,write_csv

import sys
import os
#Run NEAI CLI
import subprocess
import time
import json

import numpy as np

#NEAI_CLI_path = '/home/louis/Desktop/neai_cli_unix_v2021.03.05.1/neai_cli'
#NEAI_CLI_path = '/home/louis/Desktop/neai_cli_unix_v2021.05.03.2/neai_cli'
NEAI_CLI_path = '/home/ludusmagnus/Desktop/neai_cli_unix_v2021.05.14.1/neai_cli'
#NEAI_CLI_path = '/home/louis/Desktop/neai_cli_unix_v2021.03.22.2/neai_cli'


def data_org_run(args, files_in_opt=[]):
	if files_in_opt != []:
		args.files_in = files_in_opt
	nbr_files = len(args.files_in)
	file_out_names = []
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
		train_name = name_out_file(args.output_file, buffer_size, train_val='train', freq=args.freq)
		write_csv(train_name,train)
		if args.split > 0:
			val = np.concatenate(dfs['val'])
			val_name = name_out_file(args.output_file, buffer_size, train_val='validation', freq=args.freq)
			write_csv(val_name,val)
		file_out_names.append(train_name)
	
	return file_out_names

def NEAI_AD(train_files,nbr_axis,root_name,MCU,RAM,value_delimiter,search_time,signal_length,freq,nbr_cores=7):
	algo_type = "anomaly_detection"#'classification'
	project_Name = root_name+'-'+'AD'+'-'+str(signal_length)+'-F'+str(freq)
	
	#print('Project Name: ',project_Name)
	
	#Start NEAI engine
	result = subprocess.Popen([NEAI_CLI_path,#str('.'+NEAI_CLI_path[NEAI_CLI_path.rfind('/'):]),
								'engine',
								'-launch',
								],cwd=NEAI_CLI_path[:NEAI_CLI_path.rfind('/')],stdout=subprocess.PIPE)

	time.sleep(int(21))
	
	result = subprocess.run([NEAI_CLI_path,
							'engine',
							'-set',
							'-workspace',
							'/home/louis/Documents/workspaceNanoEdgeAi/',
							],stdout=subprocess.PIPE)
	#print("Post launch workspace set: ",result.stdout,'\n')

	#print('launch')
	result = subprocess.run([NEAI_CLI_path,
							'engine',
							'-test',
							],stdout=subprocess.PIPE)
	#print("Post launch engine check: ",result.stdout,'\n')

	#Display settings
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'display',
							'-print','-no_pretty_print',
							],stdout=subprocess.PIPE)
	#print('display settings change')
	#Create project
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'project',
							'-create',
							str('-'+algo_type),
							'-slug_name',project_Name,
							'-mcu',MCU,
							'-max_ram',str(RAM),
							'-max_flash',str(512000),
							'-number_axis',str(nbr_axis),
							],stdout=subprocess.PIPE)
	#print("project creation: ",result.stdout)
	#print()

	signals_used = ''
	signal_nbr = 1
	signal_id = str(signal_nbr)
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'signal',
							'-import',
							'-file_path',train_files[0],
							'-nominal',#'-class', '-name', os.path.basename(file),
							'-delimiter',value_delimiter,
							'-id', signal_id,
							'-project',project_Name,
							],stdout=subprocess.PIPE)

	signals_used = signal_id

	signal_nbr = 2
	signal_id = str(signal_nbr)
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'signal',
							'-import',
							'-file_path',train_files[1],
							'-anomaly',#'-class', '-name', os.path.basename(file),
							'-delimiter',value_delimiter,
							'-id', signal_id,
							'-project',project_Name,
							],stdout=subprocess.PIPE)
	signals_used = signals_used + ',' + signal_id
	

	

	#Launch optimization
	#print(signals_used)
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'optimization',
							'-launch',
							str('-signals='+signals_used),
							'-project',project_Name,
							'-nb_cores', str(nbr_cores),
							],stdout=subprocess.PIPE)
	#print('Launch: ',json.loads(result.stdout))
	#time.sleep(5)
	opt_id = int(json.loads(result.stdout)['optimization']['id'])
	#print()

	iteration = 0
	progress = 0
	while (iteration < search_time/15) and progress < 1:
		time.sleep(int(10))
		result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
								'optimization',
								'-progress',
								'-id', str(opt_id),
								'-project',project_Name,
								],stdout=subprocess.PIPE)
		try:
			progress = float(json.loads(result.stdout)['progress'])
		except Exception as e:
			print("Search status: ",result.stdout)
		iteration += 1

	#Stop optimization
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'optimization',
							'-stop',
							],stdout=subprocess.PIPE)
	#print(result.stdout)#display_results(result)

	#Get results
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'optimization',
							'-result',
							'-id',str(opt_id),
							'-project',project_Name,
							],stdout=subprocess.PIPE)
	results_dic = json.loads(result.stdout)
	#print('Precision',results_dic['precision'])
	#print('Confidence',results_dic['confidence'])
	#print('RAM',results_dic['estimated_ram'])

	#Delete project
	# result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
	# 						'project',
	# 						'-delete',
	# 						'-slug_name',args.project_Name,
	# 						],stdout=subprocess.PIPE)
	#print(result.stdout)#display_results(result)

	#Stop NEAI engine
	result = subprocess.run([NEAI_CLI_path,
							'engine',
							'-shutdown',
							],stdout=subprocess.PIPE)
	time.sleep(int(5))

	return results_dic

def NEAI_CLF(train_files,nbr_axis,root_name,MCU,RAM,value_delimiter,search_time,signal_length,freq,nbr_cores=7):
	algo_type = 'classification'
	project_Name = root_name+'-'+'CLF'+'-'+str(signal_length)+'-F'+str(freq)

	#print('Project Name: ',project_Name)
	
	#Start NEAI engine
	result = subprocess.Popen([NEAI_CLI_path,#str('.'+NEAI_CLI_path[NEAI_CLI_path.rfind('/'):]),
								'engine',
								'-launch',
								],cwd=NEAI_CLI_path[:NEAI_CLI_path.rfind('/')],stdout=subprocess.PIPE)
	#print(result)
	
	time.sleep(int(21))

	result = subprocess.run([NEAI_CLI_path,
							'engine',
							'-set',
							'-workspace',
							'/home/louis/Documents/workspaceNanoEdgeAi/',
							],stdout=subprocess.PIPE)

	#print('launch')
	result = subprocess.run([NEAI_CLI_path,
							'engine',
							'-test',
							],stdout=subprocess.PIPE)
	#print("Post launch engine check: ",result.stdout,'\n')

	#Display settings
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'display',
							'-print','-no_pretty_print',
							],stdout=subprocess.PIPE)

	#print('display settings change')
	#Create project
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'project',
							'-create',
							str('-'+algo_type),
							'-slug_name',project_Name,
							'-mcu',MCU,
							'-max_ram',str(RAM),
							'-max_flash',str(512000),
							'-number_axis',str(nbr_axis),
							],stdout=subprocess.PIPE)
	#print("project creation: ",result.stdout)
	#print()

	signals_used = ''
	signal_nbr = 1
	for file in train_files:
		signal_id = str(signal_nbr)
		result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
								'signal',
								'-import',
								'-file_path',file,
								'-class', '-name', os.path.basename(file),
								'-delimiter',value_delimiter,
								'-id', signal_id,
								'-project',project_Name,
								],stdout=subprocess.PIPE)

		#time.sleep(100)
		if signal_nbr == 1: signals_used = signal_id
		else: signals_used = signals_used + ',' + signal_id
		signal_nbr = signal_nbr + 1
		#print("Signal import",result)
		#print(signal_nbr, file)
	#Launch optimization
	#print(signals_used)
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'optimization',
							'-launch',
							str('-signals='+signals_used),
							'-project',project_Name,
							'-nb_cores', str(nbr_cores),
							],stdout=subprocess.PIPE)
	#print('Launch: ',json.loads(result.stdout))
	#time.sleep(5)
	opt_id = int(json.loads(result.stdout)['optimization']['id'])
	#print()

	iteration = 0
	progress = 0
	while (iteration < search_time/15) and progress < 1:
		time.sleep(int(10))
		result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
								'optimization',
								'-progress',
								'-id', str(opt_id),
								'-project',project_Name,
								],stdout=subprocess.PIPE)
		try:
			progress = float(json.loads(result.stdout)['progress'])
		except Exception as e:
			print("Search status: ",result.stdout)
		iteration += 1

	#Stop optimization
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'optimization',
							'-stop',
							],stdout=subprocess.PIPE)
	#print(result.stdout)#display_results(result)

	#Get results
	result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
							'optimization',
							'-result',
							'-id',str(opt_id),
							'-project',project_Name,
							],stdout=subprocess.PIPE)
	results_dic = json.loads(result.stdout)
	#print('Precision',results_dic['precision'])
	#print('Confidence',results_dic['confidence'])
	#print('RAM',results_dic['estimated_ram'])

	#Delete project
	# result = subprocess.run([NEAI_CLI_path,#str('.'+NEAI_CLI_path),
	# 						'project',
	# 						'-delete',
	# 						'-slug_name',args.project_Name,
	# 						],stdout=subprocess.PIPE)
	#print(result.stdout)#display_results(result)

	#Stop NEAI engine
	result = subprocess.run([NEAI_CLI_path,
							'engine',
							'-shutdown',
							],stdout=subprocess.PIPE)
	time.sleep(int(5))

	return results_dic


def Ys_gen(noms,abns,nom_path_root,abn_path_root):
	#Organize files all in one
	nominal_files = []
	for fold in noms:
		nom_path = os.path.join(nom_path_root,fold)
		for f in os.listdir(nom_path):
			if os.path.isfile(os.path.join(nom_path, f)):
				nominal_files.append(os.path.join(nom_path, f))
	
	abnormal_files = []
	for fold in abns:
		abn_path = os.path.join(abn_path_root,fold)
		for f in os.listdir(abn_path): 
			if os.path.isfile(os.path.join(abn_path, f)):
				abnormal_files.append(os.path.join(abn_path, f))

	return nominal_files, abnormal_files

def run_AD_CLF(args,signal_length,freq,Y,nominal_files,abnormal_files,root_name,MCU,RAM,search_time,result_path,Y_name,nbr_cores):
	args.buffer_sizes = [signal_length]
	args.freq = freq
	args.output_file = '/media/ludusmagnus/b3008e59-6246-4c41-a0ce-b9090b4d8f99/data_trans/nom_'+Y+'.csv'#'/home/louis/Desktop/John Deere/Bearing Failure/Data_trans/nom_'+Y+'.csv'
	
	try:
		file_nominal = data_org_run(args,nominal_files)
	except Exception as e:
		print('Step1: ',e)
		return
	
	args.output_file = '/media/ludusmagnus/b3008e59-6246-4c41-a0ce-b9090b4d8f99/data_trans/abn_'+Y+'.csv'
	try:
		file_abnormal = data_org_run(args,abnormal_files)
	except Exception as e:
		print('Step2: ',e)
		return
	
	try:
		results_dic = NEAI_AD([file_nominal[0],file_abnormal[0]],args.nbr_axis,root_name,MCU,RAM,args.value_delimiter,search_time,signal_length,freq,nbr_cores)
	except Exception as e:
		print('Step3: ',e)
		return
	print('AD')
	print(file_nominal)
	print('signal_length',signal_length)
	print('freq',freq)
	print('Precision',results_dic['precision'])
	print('Confidence',results_dic['confidence'])
	print()

	with open(result_path.split('.')[0]+'_AD.csv', 'a') as f:
		#'Y,Buffer_length,Subsampling,Precision,Confidence,Source_file_nom,Source_file_abn'
		f.write(str(Y+','+Y_name+','+str(signal_length)+','+str(freq)+','+str(results_dic['precision'])+','+str(results_dic['confidence'])+','+file_nominal[0]+','+file_abnormal[0]+'\n'))

	try:
		results_dic = NEAI_CLF([file_nominal[0],file_abnormal[0]],args.nbr_axis,root_name,MCU,RAM,args.value_delimiter,search_time,signal_length,freq,nbr_cores)
	except Exception as e:
		print('Step4: ',e)
		return
	print('CLF')
	print(file_nominal)
	print('signal_length',signal_length)
	print('freq',freq)
	print('Precision',results_dic['precision'])
	print('Confidence',results_dic['confidence'])
	print()

	
	with open(result_path.split('.')[0]+'_CLF.csv', 'a') as f:
		#'Y,Buffer_length,Subsampling,Precision,Confidence,Source_file_nom,Source_file_abn'
		f.write(str(Y+','+Y_name+','+str(signal_length)+','+str(freq)+','+str(results_dic['precision'])+','+str(results_dic['confidence'])+','+file_nominal[0]+','+file_abnormal[0]+'\n'))


def main():
	result_path ='report_Paderborne.csv'

	noms = ['K001CSV/','K002CSV/','K003CSV/','K004CSV/','K005CSV/','K006CSV/']
	abns = ['KA04CSV/','KA15CSV/','KA22CSV/','KA30CSV/','KB23CSV/','KB24CSV/','KB27CSV/','KI04CSV/','KI14CSV/','KI16CSV/','KI17CSV/','KI18CSV/','KI21CSV/']

	#Grab command from cli
	args = read_args()

	with open(result_path, 'a') as f:
		f.write('Y,Y_subselection,Buffer_length,Subsampling,Precision,Confidence,Source_file_nom,Source_file_abn\n')

	# for noms in noms_:
	# 	noms = [noms]
	nbr_cores = 26

	for Y in ['Y12','Y3','Y2','Y1','Y123']:

		#Data source
		nom_path_root = '/media/ludusmagnus/b3008e59-6246-4c41-a0ce-b9090b4d8f99/paderborn_csv/'+Y+'/'#'/home/louis/Desktop/John Deere/Bearing Failure/Data/paderborn_csv/'+Y+'/'
		abn_path_root = '/media/ludusmagnus/b3008e59-6246-4c41-a0ce-b9090b4d8f99/paderborn_csv/'+Y+'/'#'/home/louis/Desktop/John Deere/Bearing Failure/Data/paderborn_csv/'+Y+'/'

		root_name = 'JD-AUTO-'+Y
		args.nbr_axis = 1
		if Y == 'Y12': args.nbr_axis = 2
		if Y == 'Y123': args.nbr_axis = 3

		# signal_lengths = [16,32,64]
		# freqs = [1024,2048,4096]

		freqs_signL = [[2048,64],[32,4096],[64,1024],[32,2048],[64,2048]]

		MCU = 'cortex-m4'
		RAM = 128000
		search_time = int(3600*3)

		# for freq in freqs:
		# 	for signal_length in signal_lengths:
		for freq, signal_length in  freqs_signL:

			#for Yc in range(len(noms)+len(abns)+1):
			Y_name = "Y-full"
			nominal_files, abnormal_files = Ys_gen(noms,abns,nom_path_root,abn_path_root)

			print(Y,Y_name,freq,signal_length)
			root_name_ = root_name+Y_name
			run_AD_CLF(args,signal_length,freq,Y,nominal_files,abnormal_files,root_name_,MCU,RAM,search_time,result_path,Y_name,nbr_cores)

			for n in range(len(noms)):
				Y_name = noms[n][:-1]
				nominal_files, abnormal_files = Ys_gen([noms[n]],abns,nom_path_root,abn_path_root)
				print(Y,Y_name,freq,signal_length)
				root_name_ = root_name+Y_name
				run_AD_CLF(args,signal_length,freq,Y,nominal_files,abnormal_files,root_name_,MCU,RAM,search_time,result_path,Y_name,nbr_cores)


			for a in range(len(abns)):
				Y_name = abns[a][:-1]
				nominal_files, abnormal_files = Ys_gen(noms,[abns[a]],nom_path_root,abn_path_root)
				print(Y,Y_name,freq,signal_length)
				root_name_ = root_name+Y_name
				run_AD_CLF(args,signal_length,freq,Y,nominal_files,abnormal_files,root_name_,MCU,RAM,search_time,result_path,Y_name,nbr_cores)


			

		#

main()
