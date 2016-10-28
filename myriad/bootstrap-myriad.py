import argparse
import glob
import importlib
import libmyriad
import logging
import myriad
import os
import requests
import shutil
import subprocess
import sys
import time

class Bootstrap:

	def __init__(self):
		self.server = 'https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/'
		self.version = '1.0'

	def downloadMyriad(self):
		self.downloadMyriadFile('libmyriad.py')
		self.downloadMyriadFile('myriad.py')
		importlib.reload(libmyriad)
		importlib.reload(myriad)

	def downloadMyriadFile(self, filename):
		r = requests.get(self.server + filename)
		f = open(filename, 'w')
		f.write(r.text)
		f.flush()
		f.close()

	def run(self, jobGroup=None, jobCategory=None):
		logging.info("Job group = " + str(jobGroup))
		logging.info("Job category = " + str(jobCategory))
		result = libmyriad.ResultCode.success
		while(True):

			# run a myriad job
			m = myriad.Myriad()
			result = m.runOnce(jobGroup, jobCategory)

			if result == libmyriad.ResultCode.shutdown:
				logging.info('Shutting down myriad...')
			elif result == libmyriad.ResultCode.success:
				# If success, upload job folder(s) to S3 and delete from local drive
				logging.info('Job completed. Zipping output files')
				zips = glob.glob("*.zip")
				for zip in zips:
					command = "aws s3 cp " + str(zip) + " s3://myriaddropbox/"
					process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
					command = "rm " + str(zip)
					process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
			elif result == libmyriad.ResultCode.failure:
				logging.info('Job failed. Retrying in 10 seconds...')
				time.sleep(10)
			elif result == libmyriad.ResultCode.noaction:
				# this file should be created by the start-up script or manually by the user
				# Or it may be created by Myriad if it detects a Spot Instance being terminated
				if os.path.isfile('shutdown.myriad'):
					logging.info('Shutdown requested...')
					command = "/sbin/shutdown -h +1"
					process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
				logging.info('No jobs found. Retrying in 60 seconds...')
				time.sleep(60)

			if os.path.isfile('die.myriad') or os.path.isfile('shutdown.myriad'):
				return
			while os.path.isfile('pause.myriad'):
				time.sleep(5)

			# Download a (potentially) updated copy of Myriad
			self.downloadMyriad()

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--group', dest='group', action='store', type=str, help='Optional group for filtering the requested job')
parser.add_argument('--subGroup', dest='subGroup', action='store', type=str, help='Optional sub group for filtering the requested job')
args = parser.parse_args()

logging.basicConfig(filename='myriad.log',level=logging.INFO)
logging.basicConfig(format='%(asctime)s %(message)s')
logging.info("Bootstrapping Myriad...")

b = Bootstrap()
b.run(args.group, args.subGroup)
