from libmyriad import ResultCode
import datetime
import json
import logging
import multiprocessing
import os
import psutil
import re
import requests
import shutil
import subprocess
import time
import zipfile

class Myriad:
	
	def __init__(self):
		self.config = []
		self.maestroAPIGateway = None
		self.myriadJobsFolderOnAWS = None
		self.cpus = 1
		self.mem = 1
		self.displacements = None
		self.jobID = None
		self.executionID = None
		self.jobGroup = None
		self.jobCategory = None
		self.jobFolder = None
		self.errors = []
		self.ip = None
		self.jobConfig = None
		self.parsedJob = None
		self.jobStarted = None
		self.jobName = None
		self.ami = None
		self.instanceID = None
		self.region = None

	def getInstanceID(self):
		# Load the configuration values from file
		f = open('instance-id.txt')
		lines = f.readlines()
		f.close()
		self.instanceID = lines[0].strip()

	def getAmi(self):
		# Load the configuration values from file
		f = open('ami-id.txt')
		lines = f.readlines()
		f.close()
		self.ami = lines[0].strip()

	def getRegion(self):
		# lazy load region value
		if self.region == None:
			r = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document')
			if r.status_code == 200:
				j = json.loads(r.text)
				self.region = str(j['region'])
		return self.region

	def loadEndpoints(self):
		# Load the configuration values from file
		f = open('config.txt')
		lines = f.readlines()
		f.close()
		for line in lines:
			if line.startswith('Maestro_api_gateway '):
				self.maestroAPIGateway = line.split(' ')[1].strip()
				logging.info('JobRunner GET endpoint set to ' + self.maestroAPIGateway)
			elif line.startswith('Myriad_AWS '):
				self.myriadJobsFolderOnAWS = line.split(' ')[1].strip()
				logging.info('Myriad AWS endpoint set to ' + self.myriadJobsFolderOnAWS)

	def getJob(self, jobGroup=None, jobCategory=None):
		logging.info("Requesting a new job from " + str(self.maestroAPIGateway))
		if jobGroup != None and jobCategory != None:
			logging.info("Job group set to " + str(jobGroup))
			logging.info("Job category set to " + str(jobCategory))
			p = {"jobGroup": jobGroup, "jobCategory": jobCategory}
			r = requests.get(self.maestroAPIGateway, params=p)
		elif jobGroup != None and jobCategory == None:
			logging.info("Job group set to " + str(jobGroup))
			p = {"jobGroup": jobGroup}
			r = requests.get(self.maestroAPIGateway, params=p)
		elif jobGroup == None and jobCategory != None:
			logging.info("Job category set to " + str(jobCategory))
			p = {"jobCategory": jobCategory}
			r = requests.get(self.maestroAPIGateway, params=p)
		else:
			logging.info("No job group or sub group specified")
			r = requests.get(self.maestroAPIGateway)

		# Check for good HTTP response
		if r.status_code == 200:
			logging.info("*** Begin get job response ***")
			logging.info(r.text)
			logging.info("*** End get job response ***")

			# Check for logical error in response
			if not "errorMessage" in r.text:
				logging.info("Good response:\n" + str(r.text))
				return self.parseJob(r.text)
			else:
				# logic error
				logging.warn("Error from web service:\n" + str(r.text))
				return ResultCode.failure
		else:
			# HTTP error
			logging.warn("HTTP error: " + str(r.status_code))
			return ResultCode.failure

	def parseJob(self, job):
		# The response should look something like this...
		#	{
		#	  "JobID": "12345",
		#	  "JobGroup": "NS2",
		#	  "JobCategory": "5Z",
		#	  "JobName": "NS2-5Z-1",
		#	  "JobDefinition": {"Displacements":"-1,-1,-2"},
		#	  "Created": "2016-07-17 15:26:45"
		#	}
		logging.info("Parsing job")
		self.parsedJob = json.loads(job)
		self.jobID = self.parsedJob['JobID']
		self.executionID = self.parsedJob['ExecutionID']
		self.jobGroup = self.parsedJob['JobGroup']
		self.jobCategory = self.parsedJob['JobCategory']
		self.jobName = self.parsedJob['JobName']
		self.displacements = self.parsedJob['JobDefinition']['Displacements']
		return ResultCode.success

	def getJobSupportFiles(self):
		result = ResultCode.success
		# download job-specific script(s) to the parent folder
		url = self.myriadJobsFolderOnAWS + "/" + self.jobGroup + "/jobConfig.py"
		logging.info("Retrieving job config from " + url)
		r = requests.get(url)

		# Check for web errors (404, 500, etc.)
		if "<html>" in r.text:
			logging.warn("Bad jobConfig.py")
			result = ResultCode.failure
		# logging.info(r.text)

		f = open("jobConfig.py", "w")
		f.write(r.text)
		f.flush()
		f.close()
		return result

	def getSystemSpecs(self):
		self.cpus = psutil.cpu_count()
		logging.info('Number of cores set to ' + str(self.cpus))
		os.environ["OMP_NUM_THREADS"] = str(self.cpus)
		os.environ["MKL_NUM_THREADS"] = str(self.cpus)
		self.mem = psutil.virtual_memory().available
		logging.info('Bytes of available memory ' + str(self.mem))

	def recordDiskUsage(self):
		myoutput = open('diskspace.out', 'w')
		df = subprocess.Popen("df", stdout=myoutput)
		myoutput.flush()
		myoutput.close()
		
	def shutdownMyriad(self):
		logging.info("shutdownMyriad() invoked")
		if os.path.isfile('../shutdown.myriad'):
			logging.info('shutdownMyriad() found shutdown file. Returning True')
			return True
		r = requests.get('http://169.254.169.254/latest/meta-data/spot/termination-time')
		if r.status_code == 200:
			if re.search('.*T.*Z', r.text):
				logging.info('shutdownMyriad() determined that AWS is terminating this spot instance. Returning True')
				f = open('../shutdown.myriad', 'w')
				f.write(' ')
				f.flush()
				f.close()
				return True
		return False

	def runPsi4(self):
		self.jobStarted = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		result = ResultCode.success
		myoutput = open('psi4.out', 'w')
		myerror = open('psi4.err', 'w')
		exitcode = 0
		try:
			self.postJobStatus(True, "Started")
			p = subprocess.Popen("psi4", stdout=myoutput, stderr=myerror)
			waiting = True
			waitCounter = 0
			shutdown = False
			while waiting:
				try:
					exitcode = p.wait(5)
					logging.info("Call to p.wait() completed")
					waiting = False
				except subprocess.TimeoutExpired:
					waiting = True
					waitCounter = waitCounter + 1
					if self.shutdownMyriad():
						p.kill()
						self.postJobStatus(True, "Terminated")
						exitcode = 1
						shutdown = True
						waiting = False
					else:
						if waitCounter == 60:
							waitCounter = 0
							self.postJobStatus(True, "Running")

			logging.info("psi4 exited with exit code of " + str(exitcode))
			if exitcode == 0:
				result = ResultCode.success
			else:
				if shutdown:
					logging.info('Setting result code to ResultCode.shutdown')
					result = ResultCode.shutdown
				else:
					result = ResultCode.failure

		except RuntimeError as e:
			self.postJobStatus(False, str(e))
			result = ResultCode.failure

		finally:
			myoutput.flush()
			myerror.flush()
			myoutput.close()
			myerror.close()
			self.recordDiskUsage()
			
		return result

	def uploadResults(self):
		logging.info("Extracting results from output.dat")
		f = open("output.dat", "r")
		lines = f.readlines()
		energy = None
		for line in reversed(lines):
			if "CURRENT ENERGY" in line:
				energy = line.split(">")
				energy = energy[1].strip()
				break
		f.close()
		logging.info("Energy = " + str(energy))
		if energy == None:
			logging.warn("No energy found")
			return ResultCode.failure

		logging.info("Posting results to the web service at " + str(self.maestroAPIGateway))
		n = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		j = { "JobID" : self.jobID, "Started" : self.jobStarted, "Completed" : n, "JobResults" : energy, "job" : self.parsedJob }
		logging.info("Job results encoded as: " + str(j))
		r = requests.post(self.maestroAPIGateway, json=j)
		# Check for good HTTP response
		if r.status_code == 200:
			# Check for logical error in response
			if not "errorMessage" in r.text:
				logging.info("Good response:\n" + str(r.text))
			else:
				# logic error
				logging.warn("Error from web service:\n" + str(r.text))
				return ResultCode.failure
		else:
			# HTTP error
			logging.warn("HTTP error: " + str(r.status_code))
			return ResultCode.failure

	def clearScratch(self):
		logging.info("Clearing the scratch folder. Some errors are normal.")
		folder = os.environ['PSI_SCRATCH']
		for the_file in os.listdir(folder):
			file_path = os.path.join(folder, the_file)
			try:
				if os.path.isfile(file_path):
					os.unlink(file_path)
				elif os.path.isdir(file_path):
					shutil.rmtree(file_path)
			except Exception as e:
				logging.warn(e)
		logging.info("Finished clearing the scratch folder.")

	def makeJobFolder(self):
		self.jobFolder = self.jobName + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S_"+str(self.jobID))
		os.mkdir(self.jobFolder)
		os.chdir(self.jobFolder)

	def closeJobFolder(self):
		os.chdir("..")

	def makeInputDat(self):
		# Adjust memory value in input.dat
		logging.info("Calculating memory value for input.dat...")
		newmem = "memory " + str(int((self.mem / self.cpus)/1000000)) + " MB"

		# Creates the input.dat file in the job folder
		from jobConfig import JobConfig
		self.jobConfig = JobConfig()
		intder = self.jobConfig.intderIn(self.displacements)
		if intder != None:
			f = open('intder.in', 'w')
			f.write(intder)
			f.flush()
			f.close()
		
		
			# Run Intder2005 to produce the geometries
			logging.info("Running Intder2005...")
			myinput = open('intder.in')
			myoutput = open('intder.out', 'w')
			p = subprocess.Popen("Intder2005.x", stdin=myinput, stdout=myoutput)
			p.wait()
			myoutput.flush()
			myoutput.close()
			logging.info("Finished running Intder2005...")

			# Read the intder output and produce an input.dat file from the geometries
			logging.info("Reading file07...")
			f = open('file07')
			file07 = f.readlines()
			f.close
		else:
			file07 = None

		if len(self.errors) > 0:
			inputdat = self.jobConfig.inputDat(newmem, self.jobCategory, file07, self.errors[-1])
		else:
			inputdat = self.jobConfig.inputDat(newmem, self.jobCategory, file07)

		# Write input.dat contents to file
		f=open('input.dat', 'w')
		f.write(inputdat)
		# Append print_variables() call as a preventive measure, since that is
		#    where we get the final energy value.
		f.write("\nprint_variables()\n")
		f.flush()
		f.close()
		logging.info("File input.dat written to disk.")

	def postJobStatus(self, status, message=None):
		n = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		logging.info("Posting job status to " + str(self.maestroAPIGateway))
		if status == True:
			statusStr = "Success"
		else:
			statusStr = "Failure"
		if message == None:
			j = { "ExecutionID" : self.executionID, "LastUpdate":n, "Status":statusStr, "job" : self.parsedJob }
		else:
			j = { "JobID" : self.jobID, "LastUpdate":n, "Status":statusStr, "Message":message, "job" : self.parsedJob }
		logging.info("Job status encoded as: " + str(j))
		try:
			r = requests.put(self.maestroAPIGateway, json=j)
		except:
			logging.warn("Error posting status. Ignoring.")

	def zipJobFolder(self):
		# Get IP address
		f = open('ip.txt')
		self.ip = f.readline()
		f.close()
		if self.ip == None:
			self.ip = ""
		
		try:
			logging.info("Compressing job folder...")
			myZipFile = zipfile.ZipFile("ip_" + self.ip + "_" + self.jobFolder + ".zip", "w" )
			listing = os.listdir(self.jobFolder)
			for f in listing:
				myZipFile.write(self.jobFolder + "/" + f)
			myZipFile.close()
			logging.info("Job folder compressed. Removing original...")
			shutil.rmtree(self.jobFolder)
			logging.info("Done removing original job folder")
		except Exception as e:
			logging.warn("Error compressing job folder: " + str(e))
			

	def doModifyTag(self, action, key, value):
		# aws ec2 delete-tags --resources ami-78a54011 --region us-east-1 --tags Key=Stack
		# aws ec2 create-tags --resources ami-78a54011 --region us-east-1 --tags Key=Stack,Value=foo
		# 'Key="ExecutionID",Value="3bd99202-5d7f-49c2-a350-f1fdf2235ad3"'
		command = "aws ec2 " + action + " --resources " + str(self.instanceID) + " --region " + str(self.getRegion()) + " --tags 'Key="+str(key)
		if value != None:
			command += ',Value="' + str(value) + '"'
		command += "'"
		logging.info("Invoking " + str(command))
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = process.communicate()
		if out:
			logging.info("doModifyTag() subprocess.Popen stdout...")
			logging.info(out)
		if err:
			logging.warn("doModifyTag() subprocess.Popen stderr...")
			logging.warn(err)
		logging.info("doModifyTag() subprocess.Popen returncode...")
		logging.info(process.returncode)

	def tagInstance(self):
		self.downloadCredentials()
		self.doModifyTag("create-tags", "Name", self.jobName)
		self.doModifyTag("create-tags", "ExecutionID", self.executionID)
		self.doModifyTag("create-tags", "JobID", self.jobID)
		self.doModifyTag("create-tags", "StartTime", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		self.doModifyTag("create-tags", "Displacements", self.displacements)
		#self.displacements
	
	def untagInstance(self):
		self.downloadCredentials()
		self.doModifyTag("delete-tags", "Name", None)
		self.doModifyTag("delete-tags", "ExecutionID", None)
		self.doModifyTag("delete-tags", "JobID", None)
		self.doModifyTag("delete-tags", "StartTime", None)
		self.doModifyTag("delete-tags", "Displacements", None)
	
	def downloadCredentials(self):
		logging.info("Retrieving credentials...")
		r = requests.get("http://169.254.169.254/latest/meta-data/iam/security-credentials/S3FullAccess")
		if r.status_code == 200:
			j = json.loads(r.text)
			os.environ["AWS_ACCESS_KEY_ID"] = str(j['AccessKeyId'])
			os.environ["AWS_SECRET_ACCESS_KEY"] = str(j['SecretAccessKey'])
			os.environ["AWS_SECURITY_TOKEN"] = str(j['Token'])
			logging.info("Credentials exported to environment variables")
		else:
			logging.warn("Failed to retrieve credentials")

	def uploadOutputFiles(self):
		self.downloadCredentials()
		logging.info('Uploading output files...')
		zips = glob.glob("*.zip")
		for zip in zips:
			command = "aws s3 cp " + str(zip) + " s3://myriaddropbox/"
			process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
			command = "rm " + str(zip)
			process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)

	# Main
	def runOnce(self, jobGroup=None, jobCategory=None, error=None):
		logging.info("Myriad.runOnce invoked...")
		logging.info("Job group = " + str(jobGroup))
		logging.info("Job sub group = " + str(jobCategory))
		logging.info("Error = " + str(error))
		self.jobGroup = jobGroup
		self.jobCategory = jobCategory

		# if we have seen this error before, bail out.
		# We couldn't fix it the first time. Why should this time be any different?
		if error != None and error in self.errors:
			self.postJobStatus(False, "Error repeated: " + str(error))
			return ResultCode.failure
		
		# add the error condition to the stack of prior errors if we've never seen it before
		if error != None:
			self.errors.append(error)

		# load the endpoints for web service calls and get ami-id for this machine
		self.loadEndpoints()
		self.getAmi()
		self.getInstanceID()

		# if no error, get a new job.
		# if there is an error code, we're going to re-run the job we have
		if error == None:
			result = self.getJob(self.jobGroup, self.jobCategory)
		else:
			logging.info("Running current job again to correct for errors")
			result = ResultCode.success

		if result == ResultCode.success:
			newerror = None
			result = self.getJobSupportFiles()
			if result == ResultCode.success:
				self.getSystemSpecs()
				self.clearScratch()
				self.makeJobFolder()
				self.makeInputDat()
				self.tagInstance()
				result = self.runPsi4()
				if result == ResultCode.success:
					logging.info("runPsi4() returned success code")
					while self.uploadResults() == ResultCode.failure:
						logging.info("Failure uploading results. Retrying in 60 seconds...")
						time.sleep(60)
				else:
					if result != ResultCode.shutdown:
						# Check for known error situations in output.dat
						logging.warn("runPsi4() returned failure code. Checking for known errors")
						newerror = self.jobConfig.checkError()
						self.postJobStatus(False, "PSI4 error: " + str(newerror))
						logging.info("CheckError() result: " + str(newerror))

				self.closeJobFolder()
				if result != ResultCode.shutdown:
					self.zipJobFolder()
					self.uploadOutputFiles()
					self.clearScratch()

				# if we encounter a known error, try the job again and compensate
				if newerror != None:
					logging.info("Re-executing job due to known error: " + str(newerror))
					result = self.runOnce(self.jobGroup, self.jobCategory, newerror)
			else:
				logging.warn("Error retrieving support files")

		else:
			result = ResultCode.noaction

		return result
