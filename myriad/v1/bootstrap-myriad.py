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
		self.server = 'https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad'
		self.version = 'stable'

	def downloadMyriad(self):
		self.downloadMyriadFile('libmyriad.py')
		self.downloadMyriadFile('myriad.py')
		importlib.reload(libmyriad)
		importlib.reload(myriad)

	def downloadMyriadFile(self, filename):
		r = requests.get(self.server + "/" + self.version + "/" + filename)
		f = open(filename, 'w')
		f.write(r.text)
		f.flush()
		f.close()

	def run(self, jobGroup=None, jobCategory=None, server='https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/', version='stable'):
		logging.info("Job group = " + str(jobGroup))
		logging.info("Job category = " + str(jobCategory))
		logging.info("Server = " + str(server))
		logging.info("Version = " + str(version))

		# Download a (potentially) updated copy of Myriad
		self.server = server
		self.version = version
		self.downloadMyriad()

		# run a myriad job
		m = myriad.Myriad()
		result = m.runOnce(jobGroup, jobCategory)

		if result == libmyriad.ResultCode.shutdown or os.path.isfile('shutdown.myriad'):
			logging.info('Shutting down myriad...')
			return
		elif result == libmyriad.ResultCode.failure:
			logging.info('Job failed.')
		elif result == libmyriad.ResultCode.noaction:
			logging.info('No more jobs. Sleeping for 60 seconds...')
			# TO DO: Move this sleep to ec2-user-script-myriad.sh (Needs return codes)
			time.sleep(60)

		# Download a (potentially) updated copy of Myriad
		self.downloadMyriad()

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--group', dest='group', action='store', type=str, help='Optional group for filtering the requested job')
parser.add_argument('--subGroup', dest='subGroup', action='store', type=str, help='Optional sub group for filtering the requested job')
parser.add_argument('--server', dest='server', action='store', type=str, help='Optional server address for updating Myriad')
parser.add_argument('--version', dest='version', action='store', type=str, help='Optional version number of Myriad to update to or "stable"')
args = parser.parse_args()

logging.basicConfig(filename='myriad.log',level=logging.INFO,format='%(asctime)s %(message)s')
logging.info("Bootstrapping Myriad...")

b = Bootstrap()
b.run(jobGroup=args.group, jobCategory=args.subGroup, server=args.server, version=args.version)
