from libmyriad import ResultCode
import datetime
import json
import multiprocessing
import os
import psutil
import requests
import shutil
import subprocess
import time

class Myriad:
        
        def __init__(self):
                self.config = []
                self.maestroAPIGateway = None
                self.myriadJobsFolderOnAWS = None
                self.cpus = 1
                self.mem = 1
                self.displacements = None
                self.jobID = None
                self.jobGUID = None
                self.jobGroup = None
                self.jobSubGroup = None
                self.makeInputDatParameters = None
                self.jobFolder = None
                self.errors = []

        def loadEndpoints(self):
                # Load the configuration values from file
                f = open('config.txt')
                lines = f.readlines()
                f.close()
                for line in lines:
                        if line.startswith('Maestro_api_gateway '):
                                self.maestroAPIGateway = line.split(' ')[1].strip()
                                print('JobRunner GET endpoint set to ' + self.maestroAPIGateway)
                        elif line.startswith('Myriad_AWS '):
                                self.myriadJobsFolderOnAWS = line.split(' ')[1].strip()
                                print('Myriad AWS endpoint set to ' + self.myriadJobsFolderOnAWS)

        def getJob(self, jobGroup=None, jobSubGroup=None):
                print("Requesting a new job from " + str(self.maestroAPIGateway))
                if jobGroup != None and jobSubGroup != None:
                        print("Job group set to " + str(jobGroup))
                        print("Job sub group set to " + str(jobSubGroup))
                        p = {"jobGroup": jobGroup, "jobSubGroup": jobSubGroup}
                        r = requests.get(self.maestroAPIGateway, params=p)
                elif jobGroup != None and jobSubGroup == None:
                        print("Job group set to " + str(jobGroup))
                        p = {"jobGroup": jobGroup}
                        r = requests.get(self.maestroAPIGateway, params=p)
                elif jobGroup == None and jobSubGroup != None:
                        print("Job sub group set to " + str(jobSubGroup))
                        p = {"jobSubGroup": jobSubGroup}
                        r = requests.get(self.maestroAPIGateway, params=p)
                else:
                        print("No job group or sub group specified")
                        r = requests.get(self.maestroAPIGateway)

                # Check for good HTTP response
                if r.status_code == 200:
                        print("*** Begin get job response ***")
                        print(r.text)
                        print("*** End get job response ***")

                        # Check for logical error in response
                        if not "errorMessage" in r.text:
                                print("Good response:\n" + str(r.text))
                                return self.parseJob(r.text)
                        else:
                                # logic error
                                print("Error from web service:\n" + str(r.text))
                                return ResultCode.failure
                else:
                        # HTTP error
                        print("HTTP error: " + str(r.status_code))
                        return ResultCode.failure

        def parseJob(self, job):
                # The response should look something like this...
                #    # JobID: 527
                #    # JobGUID: b4af8ced-3661-11e6-a162-12fe8751cda9
                #    # MakeInputDatParameters: -t MTc
                #    -1,1,-2
                print("Parsing job")
                for line in job.split('\n'):
                        print('Parsing line: ' + line)
                        if line.strip() == '':
                                pass
                        elif line.strip().startswith('#'):
                                if "JobID:" in line.strip():
                                        self.jobID = line.split(':')[1].strip()
                                        print('JobID set to ' + str(self.jobID))
                                elif "JobGUID:" in line.strip():
                                        self.jobGUID = line.split(':')[1].strip()
                                        print('JobGUID set to ' + str(self.jobGUID))
                                elif "JobGroup:" in line.strip():
                                        self.jobGroup = line.split(':')[1].strip()
                                        print('JobGroup set to ' + str(self.jobGroup))
                                elif "MakeInputDatParameters:" in line.strip():
                                        self.makeInputDatParameters = line.split(':')[1].strip()
                                        print('MakeInputDatParameters set to ' + str(self.makeInputDatParameters))
                                else:
                                        self.displacements = line.strip()
                        else:
                                # Non-blank, non-commented line. Must be the displacements
                                self.displacements = line
                return ResultCode.success

        def getJobSupportFiles(self):
                result = ResultCode.success
                # download job-specific script(s) to the parent folder
                url = self.myriadJobsFolderOnAWS + "/" + self.jobGroup + "/jobConfig.py"
                print("Retrieving job config from " + url)
                r = requests.get(url)

                # Check for web errors (404, 500, etc.)
                if "<html>" in r.text:
                        print("Bad jobConfig.py")
                        result = ResultCode.failure
                print(r.text)

                f = open("jobConfig.py", "w")
                f.write(r.text)
                f.flush()
                f.close()
                return result

        def getSystemSpecs(self):
                self.cpus = psutil.cpu_count()
                print('Number of cores set to ' + str(self.cpus))
                os.environ["OMP_NUM_THREADS"] = str(self.cpus)
                os.environ["MKL_NUM_THREADS"] = str(self.cpus)
                self.mem = psutil.virtual_memory().available
                print('Bytes of available memory ' + str(self.mem))

        def recordDiskUsage(self):
                myoutput = open('diskspace.out', 'w')
                df = subprocess.Popen("df", stdout=myoutput)
                myoutput.flush()
                myoutput.close()

        def runPsi4(self):
                result = ResultCode.success
                myoutput = open('psi4.out', 'w')
                myerror = open('psi4.err', 'w')
                exitcode = 0
                try:
                        p = subprocess.Popen("psi4", stdout=myoutput, stderr=myerror)
                        waiting = True
                        while waiting:
                                try:
                                        exitcode = p.wait(300)
                                        waiting = False
                                except subprocess.TimeoutExpired:
                                        waiting = True
                                        self.postJobStatus(True, "Running")

                        print("psi4 exited with exit code of " + str(exitcode))
                        if exitcode == 0:
                                result = ResultCode.success
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
                print("Extracting results from output.dat")
                f = open("output.dat", "r")
                lines = f.readlines()
                energy = None
                for line in reversed(lines):
                        if "CURRENT ENERGY" in line:
                                energy = line.split(">")
                                energy = energy[1].strip()
                                break
                f.close()
                print("Energy = " + str(energy))
                if energy == None:
                        print("No energy found")
                        return ResultCode.noaction

                print("Posting results to the web service at " + str(self.maestroAPIGateway))
                n = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                p = { "jobGUID" : self.jobGUID }
                j = { "completed" : n, "jobResults" : energy }
                r = requests.post(self.maestroAPIGateway, params=p, json=j)
                # Check for good HTTP response
                if r.status_code == 200:
                        # Check for logical error in response
                        if not "errorMessage" in r.text:
                                print("Good response:\n" + str(r.text))
                        else:
                                # logic error
                                print("Error from web service:\n" + str(r.text))
                                return ResultCode.failure
                else:
                        # HTTP error
                        print("HTTP error: " + str(r.status_code))
                        return ResultCode.failure

        def clearScratch(self):
                print("Clearing the scratch folder. Some errors are normal.")
                folder = os.environ['PSI_SCRATCH']
                for the_file in os.listdir(folder):
                        file_path = os.path.join(folder, the_file)
                        try:
                                if os.path.isfile(file_path):
                                        os.unlink(file_path)
                                elif os.path.isdir(file_path):
                                        shutil.rmtree(file_path)
                        except Exception as e:
                             print(e)                
                print("Finished clearing the scratch folder.")

        def makeJobFolder(self):
                self.jobFolder = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_"+str(self.jobID))
                os.mkdir(self.jobFolder)
                os.chdir(self.jobFolder)

        def closeJobFolder(self):
                os.chdir("..")

        def makeInputDat(self):
                # Adjust memory value in input.dat
                print("Calculating memory value for input.dat...")
                newmem = "memory " + str(int((self.mem / self.cpus)/1000000)) + " MB"

                # Creates the input.dat file in the job folder
                from jobConfig import JobConfig
                j = JobConfig()
                intder = j.intderIn(self.displacements)
                if intder != None:
                        f = open('intder.in', 'w')
                        f.write(intder)
                        f.flush()
                        f.close()
                
                
                        # Run Intder2005 to produce the geometries
                        print("Running Intder2005...")
                        myinput = open('intder.in')
                        myoutput = open('intder.out', 'w')
                        p = subprocess.Popen("Intder2005.x", stdin=myinput, stdout=myoutput)
                        p.wait()
                        myoutput.flush()
                        myoutput.close()
                        print("Finished running Intder2005...")

                        # Read the intder output and produce an input.dat file from the geometries
                        print("Reading file07...")
                        f = open('file07')
                        file07 = f.readlines()
                        f.close
                else:
                        file07 = None

                if len(self.errors) > 0:
                        inputdat = j.inputDat(newmem, self.makeInputDatParameters, file07, self.errors[-1])
                else:
                        inputdat = j.inputDat(newmem, self.makeInputDatParameters, file07)

                # Write input.dat contents to file
                f=open('input.dat', 'w')
                f.write(inputdat)
                # Append print_variables() call as a preventive measure, since that is
                #    where we get the final energy value.
                f.write("\nprint_variables()\n")
                f.flush()
                f.close()
                print("File input.dat written to disk.")

        def postJobStatus(self, status, message=None):
                n = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("Posting job status to " + str(self.maestroAPIGateway))
                p = { "jobGUID" : self.jobGUID }
                if status == True:
                        statusStr = "Success"
                else:
                        statusStr = "Failure"
                if message == None:
                        j = {"lastUpdate":n,"status":statusStr}
                else:
                        j = {"lastUpdate":n,"status":statusStr,"message":message}
                try:
                        r = requests.put(self.maestroAPIGateway, params=p, json=j)
                except:
                        print("Error posting status. Ignoring.")
                '''
                # Check for good HTTP response
                if r.status_code == 200:
                        # Check for logical error in response
                        if not "errorMessage" in r.text:
                                print("Good response:\n" + str(r.text))
                        else:
                                # logic error
                                print("Error from web service:\n" + str(r.text))
                else:
                        # HTTP error
                        print("HTTP error: " + str(r.status_code))
                '''

        def checkError(self):
                print("Opening output.dat...")
                f = open("output.dat", "r")
                lines = f.readlines()
                f.close()

                error = None
                for line in reversed(lines):
                        if "Failed to converge." in line:
                                print("Found a 'Failed to converge.' error")
                                error = "Failed to converge."
                        elif error == "Failed to converge." and " iter " in line:
                                # split the line into columns and only look at the Delta E value (fifth column)
                                chunks = line.split()
                                
                                if "e-12" in chunks[4]:
                                        print("Found a 'Failed to converge. (12)' error")
                                        error = "Failed to converge. (12)"
                                if "e-13" in chunks[4]:
                                        print("Found a 'Failed to converge. (13)' error")
                                        error = "Failed to converge. (13)"
                                break
                print("Returning error: " + str(error))
                return error

        # Main
        def runOnce(self, jobGroup=None, jobSubGroup=None, error=None):
                print("Job group = " + str(jobGroup))
                print("Job sub group = " + str(jobSubGroup))
                print("Error = " + str(error))
                self.jobGroup = jobGroup
                self.jobSubGroup = jobSubGroup

                # if we have seen this error before, bail out.
                # We couldn't fix it the first time. Why should this time be any different?
                if error != None and error in self.errors:
                        self.postJobStatus(False, "Error repeated: " + str(error))
                        return ResultCode.failure
                
                # add the error condition to the stack of prior errors if we've never seen it before
                if error != None:
                        self.errors.append(error)

                # run the job...
                self.loadEndpoints()

                # if no error, get a new job.
                # if there is an error code, we're going to re-run the job we have
                if error == None:
                        result = self.getJob(self.jobGroup, self.jobSubGroup)
                else:
                        print("Running current job again to correct for errors")
                        result = ResultCode.success

                if result == ResultCode.success:
                        newerror = None
                        result = self.getJobSupportFiles()
                        if result == ResultCode.success:
                                self.getSystemSpecs()
                                self.clearScratch()
                                self.makeJobFolder()
                                self.makeInputDat()
                                result = self.runPsi4()
                                if result == ResultCode.success:
                                        print("runPsi4() returned success code")
                                        while self.uploadResults() == ResultCode.failure:
                                                print("Failure uploading results. Retrying in 60 seconds...")
                                                time.sleep(60)
                                else:
                                        # Check for known error situations in output.dat
                                        print("runPsi4() returned failure code. Checking for known errors")
                                        newerror = self.checkError()
                                        self.postJobStatus(False, "PSI4 error: " + str(newerror))
                                        print("CheckError() result: " + str(newerror))

                                self.closeJobFolder()
                                self.clearScratch()

                                # if we encounter a known error, try the job again and compensate
                                if newerror != None:
                                        print("Re-executing job due to known error: " + str(newerror))
                                        result = self.runOnce(self.jobGroup, self.jobSubGroup, newerror)
                        else:
                                print("Error retrieving support files")

                else:
                        result = ResultCode.noaction

                return result
