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

# ******* Begin main event **********
def handler(event, context):
	# set the log function
	libtaylor.setLogFunction(info)
	libtaylor.setParseRanges(parseRanges)

	info(event)
	for record in event['Records']:
		bucket = record['s3']['bucket']['name']
		#info(bucket)
		key = record['s3']['object']['key']
		#info(key)
		download_path = '/tmp/{}{}'.format(uuid.uuid4(), key.replace('/','-'))
		upload_path_indexes = '/tmp/{}{}'.format(key.replace('/','-'), '.indexes')
		upload_path_force = '/tmp/{}{}'.format(key.replace('/','-'), '.force')
		upload_path_disp = '/tmp/{}{}'.format(key.replace('/','-'), '.disp')
		#info(download_path)
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
		info('Calculating parallelization values')
		p = e['parallel']
		if p['node'] == 1:
			sIndex = 0
			info('First node. Setting sIndex to 0')
		else:
			sIndex = libtaylor.magic(e['reps'], p['node'], p['nodes'])
			info('sIndex set to ' + str(sIndex))
		if p['node'] == p['nodes']:
			# if it's the last node in the node set, then the end is the last index
			eIndex = e['digits']**e['reps']
			info('Last node. eIndex set to ' + str(eIndex))
		else:
			eIndex = libtaylor.magic(e['reps'], p['node']+1, p['nodes'])
			info('eIndex set to ' + str(eIndex))
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
	info("sIndex="+str(sIndex))
	info("eIndex="+str(eIndex))

	main(e, sIndex, eIndex, indexes, force, disp)
