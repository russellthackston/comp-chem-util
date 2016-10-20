import math
import sys
import argparse
import csv
import itertools
import json
import logging
import boto3
import os
import uuid

s3_client = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
event = { "digits" : 5, "reps" : 12, "start" : 1, "end" : 125, "modcheck" : [{ "checkvalue" : 2, "ranges" : [{"start" : 6, "end" : 9}, {"start" : 10, "end" : 11}, {"start" : 12, "end" : 12}] }], "equivalence" : [{ "checkvalue" : 3, "ranges" : [{"start" : 6, "end" : 9}, {"start" : 10, "end" : 11}, {"start" : 12, "end" : 12}] }], "parallel" : { "node" : 5, "nodes" : 100 } }
event = { "digits" : 5, "reps" : 12, "modcheck" : [{ "checkvalue" : 2, "ranges" : [{"start" : 6, "end" : 9}, {"start" : 10, "end" : 11}, {"start" : 12, "end" : 12}] }], "equivalence" : [{ "checkvalue" : 3, "ranges" : [{"start" : 6, "end" : 9}, {"start" : 10, "end" : 11}, {"start" : 12, "end" : 12}] }] }
'''

#parser = argparse.ArgumentParser(description='Generate a Taylor series.', epilog='Example: "python taylor.py 5 24" will print the product of 24 repetitions of [0,1,2,3,4].')
#parser.add_argument("digits", help="The number of digits in the array [0..digits]", type=int)
#parser.add_argument("reps", help="The number of repetitions of the set", type=int)
#parser.add_argument("-s", "--start", help="Only print lines with indexes greater than or equal to 'start'", type=int)
#parser.add_argument("-e", "--end", help="Only print lines with indexes less than or equal to 'end'", type=int)
#parser.add_argument("-m", "--modcheck", help="Enables a mod check of one of more subsets of digits (first digit is index 1). Not passing the mod check excludes the row. Expects this value to be in the format '-m d:[s-e]' where 'd' is the mod check value, 's' is the start index, and 'e' is the end index.", type=str)
#parser.add_argument("-q", "--equivalence", help="Enables an equivalence check of one or more subsets of digits (first digit is index 1). Passing the equivalence check, after failing a mod check, includes the row. Expects this value to be in the format '-m q:[s-e]' where 'q' is the equivalence check value, 's' is the start index, and 'e' is the end index.", type=str)
#parser.add_argument("-p", "--parallel", help="Calculates the --start and --end values based on the provided node number and number of nodes. Expected format is '--p (node number):(number of nodes)'", type=str)
#parser.add_argument("-f", "--forceConstants", help="Write force constant values to force.txt", action="store_true")
#parser.add_argument("-d", "--displacements", help="Write displacement values to disp.txt", action="store_true")
#parser.add_argument("-i", "--indexes", help="Write row indexes to indexes.txt", action="store_true")
#parser.add_argument("-l", "--silent", help="Suppress all output to stdout", action="store_true")
#parser.add_argument("-u", "--unfiltered", help="Skip the filtering step and produce a complete cartesian product", action="store_true")
#parser.add_argument("-v", "--verbose", help="Produce verbose output", action="store_true")
#parser.add_argument("--debug", help="Sets up the job but does not run it. Prints debug info instead", action="store_true")
#parser.add_argument("--summary", help="Only print summary information (i.e. number of rows in output files)", action="store_true")
#parser.add_argument('--version', action='version', version='Taylor Series generation script v1.0. Latest version and full documentation available at https://github.com/russellthackston/comp-chem-util in the "misc" folder. Report any bugs or issues at the above web address.')
#args=parser.parse_args()

# This function derives a single line from the cartesian product with the index 'n'
def entry(n, digits, reps):
	combo = []
	#logger.info('# Building entry(' + str(n) + ')')
	exp=1
	while n > 0:
		div=len(digits)**exp
		digit=(n%div)
		n-=digit
		digit=digit/len(digits)**(exp-1)
		combo.insert(0,int(digit))
		exp+=1
	for i in range(0,reps-len(combo)):
		combo.insert(0,0)
	return combo

def parseRanges(rangeobj):
	# [{ "checkvalue" : 2, "ranges" : [{"start" : 6, "end" : 9}, {...}, {...}] }, {...}]

	results=dict()
	for range in rangeobj:
		num=range['checkvalue']
		ranges=range['ranges']
		results[num] = []
		for r in ranges:
			start=r['start']
			end=r['end']
			results[num].append([start,end])
	#logger.info("# Parsed range " + str(rangeobj) + " as " + str(results))
	return results

def eqCheck(e, eqchecks):
	if eqchecks == None or len(eqchecks.keys()) == 0:
		#logger.info("# No equivalence checks defined")
		return True
	#logger.info("# Equivalence checking is enabled.")
	for k in eqchecks.iterkeys():
		for r in eqchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedEq=sum(e[start-1:end]) != k
			if failedEq:
				#logger.info("# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Failed.")
				return False
			else:
				#logger.info("# Equivalence checking of " + str(k) + " for sum(" + str(sub) + "). Passed.")
				pass
	return True

def modCheck(e, modchecks):
	if modchecks == None or len(modchecks.keys()) == 0:
		#logger.info("# No mod checks defined")
		return True
	#logger.info("# Mod checking is enabled.")
	for k in modchecks.iterkeys():
		for r in modchecks[k]:
			start=r[0]
			end=r[1]
			sub=e[start-1:end]
			failedMod=sum(e[start-1:end])%k != 0
			if failedMod:
				#logger.info("# Mod checking %" + str(k) + " for " + str(sub) + ". Failed.")
				return False
			else:
				#logger.info("# Mod checking %" + str(k) + " for " + str(sub) + ". Passed.")
				pass
	return True

def displacements(e):
	#logger.info("# Converting force constants to displacements for " + str(e))
	indexes=[]
	values=[]
	for i, digit in enumerate(e):
		if digit != 0:
			indexes.append(i)
			values.append(digit)
	if len(values) == 0:
		#logger.info("# No non-zero values found in list " + str(e))
		return [e]
	#logger.info("# Non-zero value(s) " + str(values) + " located in index(es) " + str(indexes))
	prods=[]
	for i, digit in enumerate(values):
		tmp=[]
		for j in range(-1*digit,digit+1,2):
			tmp.append(j)
		prods.append(tmp)
	newrows=map(list, itertools.product(*prods))
	#logger.info("# Displacement combinations: " + str(newrows))
	# Build each new displacement row by copying the force constant row then overwriting
	#   the non-zero values with the calculated values
	result=[]
	for row in newrows:
		# make a copy of 'e'
		r=list(e)
		for i, index in enumerate(indexes):
			r[index]=row[i]
		result.append(r)
	#logger.info("# Calculated a total of " + str(len(result)) + " displacements")
	#logger.info("# Displacement list: " + str(result))
	return result

def main(event, startIndex, endIndex, indexes, force, disp):
	modchecks=None
	eqchecks=None

	# Set up summary variables
	rowsIndexes = 0
	rowsForce = 0
	rowsDisp = 0

	# Logical error checking with config
	if 'equivalence' in event and not 'modcheck' in event:
		#logger.info("# Error: equivalence check defined without mod check")
		exit(1)

	# Build the array of digits
	digits=[]
	for i in range(0, event['digits']):
		digits.append(i)
	#logger.info('# Digits array: ' + str(digits))

	# If mod checks are enabled, build a list of checks to be performed
	if 'modcheck' in event:
		modchecks=parseRanges(event['modcheck'])
		#logger.info("# Parsed mod check " + str(event['modcheck']) + " into " + str(modchecks))

	# If equivalence checks are enabled, build a list of checks to be performed
	if 'equivalence' in event:
		eqchecks=parseRanges(event['equivalence'])
		#logger.info("# Parsed mod check " + str(event['equivalence']) + " into " + str(eqchecks))

	# Open the output streams
	fIndexes = open(indexes, 'w')
	fForce = open(force, 'w')
	writerForce = csv.writer(fForce)
	fDisp = open(disp, 'w')
	writerDisp = csv.writer(fDisp)

	rowCount = 0
	i=startIndex
	while i < endIndex:
		e=entry(i, digits, event['reps'])
		#logger.info('# Processing index ' + str(i))
		old_i=i

		# Check if numbers in array total to (e['digits'] - 1) or greater and skip to next block
		if sum(e) >= (event['digits'] - 1):
			done = False
			# copy the row
			etemp = e[:]
			# zero the right-most non-zero value
			for idx in range(event['reps']-1, -1, -1):
				if etemp[idx] > 0:
					etemp[idx] = 0
					if idx > 0:
						etemp[idx-1] = etemp[idx-1] + 1
					else:
						done = True
					break
			# translate new array into an index
			if done:
				i = endIndex
			else:
				i = 0
				for idx in range(0, event['reps']):
					p = event['reps'] - idx - 1
					i += etemp[idx] * (event['digits']**p)
		else:
			i+=1
		if sum(e) <= (event['digits'] - 1):
			keeper = True

			# if a mod check is defined, run it
			if 'modcheck' in event:
				#logger.info("# Performing mod check")
				passedModCheck = modCheck(e, modchecks)
			else:
				passedModCheck = True

			# if the mod check fails, you may need to check for an Eq check
			if not passedModCheck:
				#logger.info('# Failed mod check')
				if 'equivalence' in event:
					#logger.info("# Performing equivalence check")
					passedEqCheck = eqCheck(e, eqchecks)
					if not passedEqCheck:
						#logger.info('# Failed equivalence check')
						keeper = False
				else:
					keeper = False
			if not keeper:
				#logger.info('# Bad record: ' + str(e))
				rowCount+=1
			else:
				#logger.info('# Good record: ' + str(e))
				fIndexes.write(str(i)+"\n")
				lst=displacements(e)
				for l in lst:
					writerDisp.writerow(l)
				writerForce.writerow(e)
		else:
			#logger.info('# Skipped ' + str(e) + ' due to array total greater than (e["digits"] - 1)')
			pass

	fIndexes.close()
	fDisp.close()
	fForce.close()

	logger.info('# Done creating cartesion product')

def magic(reps, node, nodes):
	return ((2*reps*node)**long((reps**2)/(21*math.sqrt(nodes))))

# ******* Begin main event **********
def handler(event, context):
	logger.info(event)
	for record in event['Records']:
		bucket = record['s3']['bucket']['name']
		#logger.info(bucket)
		key = record['s3']['object']['key']
		#logger.info(key)
		download_path = '/tmp/{}{}'.format(uuid.uuid4(), key.replace('/','-'))
		upload_path_indexes = '/tmp/{}{}'.format(key.replace('/','-'), '.indexes')
		upload_path_force = '/tmp/{}{}'.format(key.replace('/','-'), '.force')
		upload_path_disp = '/tmp/{}{}'.format(key.replace('/','-'), '.disp')
		#logger.info(download_path)
		s3_client.download_file(bucket, key, download_path)
		f = open(download_path)
        	e = f.readlines()
        	e = ' '.join(e)
        	f.close()
        	processRecord(e, upload_path_indexes, upload_path_force, upload_path_disp)
        	s3_client.upload_file(upload_path_indexes, '{}'.format(bucket), '{}{}'.format(key, '.indexes'))
        	s3_client.upload_file(upload_path_force, '{}'.format(bucket), '{}{}'.format(key, '.force'))
        	s3_client.upload_file(upload_path_disp, '{}'.format(bucket), '{}{}'.format(key, '.disp'))

def processRecord(event, indexes, force, disp):
	e = json.loads(event)
	if 'parallel' in e:
		logger.info('Calculating parallelization values')
		p = e['parallel']
		if p['node'] == 1:
			sIndex = 0
			logger.info('First node. Setting sIndex to 0')
		else:
			sIndex = magic(e['reps'], p['node'], p['nodes'])
			logger.info('sIndex set to ' + str(sIndex))
		if p['node'] == p['nodes']:
			# if it's the last node in the node set, then the end is the last index
			eIndex = e['digits']**e['reps']
			logger.info('Last node. eIndex set to ' + str(eIndex))
		else:
			eIndex = magic(e['reps'], p['node']+1, p['nodes'])
			logger.info('eIndex set to ' + str(eIndex))
		if sIndex == eIndex:
			eIndex = eIndex + 1
	else:
		if 'start' in e:
			sIndex=e['start']
		else:
			sIndex=0
		if 'end' in e:
			eIndex=e['end']
		else:
			eIndex=e['digits']**e['reps']
	logger.info("sIndex="+str(sIndex))
	logger.info("eIndex="+str(eIndex))

	main(e, sIndex, eIndex, indexes, force, disp)