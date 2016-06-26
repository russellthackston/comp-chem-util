from libmyriad import ResultCode
import requests
import multiprocessing
import psutil
import os
import subprocess
import shutil
import datetime
import json

class Myriad:
        
        def __init__(self):
                self.config = []
                self.maestroAPIGateway = ""
                self.myriadJobsFolderOnAWS = ""
                self.cpus = 1
                self.mem = 1
                self.displacements = ""
                self.jobID = ""
                self.jobGUID = ""
                self.jobGroup = ""
                self.makeInputDatParameters = ""
                self.jobFolder = ""

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

        def getJob(self):
                print("Requesting a new job from " + str(self.maestroAPIGateway))
                r = requests.get(self.maestroAPIGateway)
                # Check for good HTTP response
                if r.status_code == 200:
                        # Check for logical error in response
                        if not "errorMessage" in r.text:
                                print("Good response:\n" + str(r.text))
                                return self.parseJob(r.text.split('\n'))
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
                for line in job:
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
                # download job-specific script(s) to the parent folder
                r = requests.get(self.myriadJobsFolderOnAWS + "/" + self.jobGroup + "/jobConfig.py")
                f = open("jobConfig.py", "w")
                f.write(r.text)
                f.flush()
                f.close()

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
                myoutput = open('psi4.out', 'w')
                myerror = open('psi4.err', 'w')
                p = subprocess.Popen("psi4", stdout=myoutput, stderr=myerror)
                waiting = True
                while waiting:
                        try:
                                result = p.wait(120)
                                waiting = False
                        except subprocess.TimeoutExpired:
                                waiting = True
                                self.postJobStatus("Success")
                myoutput.flush()
                myerror.flush()
                myoutput.close()
                myerror.close()
                self.recordDiskUsage()
                if result == 0:
                        return ResultCode.success
                else:
                        return ResultCode.failure

        def uploadResults(self):
                print("Extracting results from output.dat")
                energy = self.finalEnergy(open("output.dat", "br"))
                print(energy)
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
                                return self.parseJob(r.text.split('\n'))
                        else:
                                # logic error
                                print("Error from web service:\n" + str(r.text))
                                return ResultCode.failure
                else:
                        # HTTP error
                        print("HTTP error: " + str(r.status_code))
                        return ResultCode.failure

        # This function was shamelessly stolen from a StackOverflow answer and modified to
        #   find the final energy value and return it.
        # http://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
        def finalEnergy(self, f):
                energy = ""
                BLOCK_SIZE = 1024
                f.seek(0, 2)
                block_end_byte = f.tell()
                block_number = -1
                blocks = [] # blocks of size BLOCK_SIZE, in reverse order starting
                            # from the end of the file
                found = False
                while block_end_byte > 0 and not found:
                        if (block_end_byte - BLOCK_SIZE > 0):
                                # read the last block we haven't yet read
                                f.seek(block_number*BLOCK_SIZE, 2)
                                blocks.extend(f.read(BLOCK_SIZE).decode("utf-8").split("\n"))
                        else:
                                # file too small, start from begining
                                f.seek(0,0)
                                # only read what was not read
                                blocks.extend(f.read(block_end_byte).decode("utf-8").split('\n'))
                        block_end_byte -= BLOCK_SIZE
                        block_number -= 1
                        for line in blocks:
                                if "CURRENT ENERGY" in line:
                                        found = True
                                        energy = line
                if energy.strip() != "":
                        e = energy.split(">")
                        energy = e[1].strip()
                return energy
    
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
                # Creates the input.dat file in the job folder
                from jobConfig import JobConfig
                j = JobConfig()
                intder = j.intderIn(self.displacements)
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

                # Adjust memory value in input.dat
                print("Calculating memory value for input.dat...")
                newmem = "memory " + str(int((self.mem / self.cpus)/1000000)) + " MB"

                # Read the intder output and produce an input.dat file from the geometries
                print("Reading file07...")
                f = open('file07')
                file07 = f.readlines()
                f.close
                inputdat = j.inputDat(self.makeInputDatParameters, file07, newmem)

                # Write input.dat contents to file
                f=open('input.dat', 'w')
                f.write(inputdat)
                # Append print_variables() call as a preventive measure, since that is
                #    where we get the final energy value.
                f.write("\nprint_variables()\n")
                f.flush()
                f.close()
                print("File input.dat written to disk.")

        def postJobStatus(self, status):
                '''
                {
                        "lastUpdate":"2016-06-26 17:31:38",
                        "status":"Success"
                }
                '''
                n = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("Posting job status to " + str(self.maestroAPIGateway))
                p = { "jobGUID" : self.jobGUID }
                if status == True:
                        j = {"lastUpdate":n,"status":"Success"}
                else:
                        j = {"lastUpdate":n,"status":"Failure"}
                r = requests.put(self.maestroAPIGateway, params=p, json=j)
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

        # Main
        def runOnce(self):
                self.loadEndpoints()
                result = ResultCode.success
                if self.getJob() == ResultCode.success:
                        self.getJobSupportFiles()
                        self.getSystemSpecs()
                        self.clearScratch()
                        self.makeJobFolder()
                        self.makeInputDat()
                        result = self.runPsi4()
                        if result == ResultCode.success:
                                self.uploadResults()
                        else:
                                self.postJobStatus(False)
                        self.closeJobFolder()
                        self.clearScratch()
                else:
                        result = ResultCode.noaction
                return result
