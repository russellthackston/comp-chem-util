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

import libtaylor

s3_client = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
event = { "digits" : 5, "reps" : 12, "start" : 1, "end" : 125, "modcheck" : [{ "checkvalue" : 2, "ranges" : [{"start" : 6, "end" : 9}, {"start" : 10, "end" : 11}, {"start" : 12, "end" : 12}] }], "equivalence" : [{ "checkvalue" : 3, "ranges" : [{"start" : 6, "end" : 9}, {"start" : 10, "end" : 11}, {"start" : 12, "end" : 12}] }], "parallel" : { "node" : 5, "nodes" : 100 } }
event = { "digits" : 5, "reps" : 12, "modcheck" : [{ "checkvalue" : 2, "ranges" : [{"start" : 6, "end" : 9}, {"start" : 10, "end" : 11}, {"start" : 12, "end" : 12}] }], "equivalence" : [{ "checkvalue" : 3, "ranges" : [{"start" : 6, "end" : 9}, {"start" : 10, "end" : 11}, {"start" : 12, "end" : 12}] }] }
'''

def info(msg):
	logger.info(msg)

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
	info("# Parsed range " + str(rangeobj) + " as " + str(results))
	return results

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
		e=libtaylor.entry(i, digits, event['reps'])
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
			# Failing the mod check but passing the Eq check will get the record included
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
