from libmyriad import ResultCode
import requests
import multiprocessing
import psutil
import os
import subprocess

class Myriad:
        config = []
        jobrunnerGET = ""
        outputPOST = ""
        cpus = 1
        mem = 1
        
        def __init__(self):
                config = []
                jobrunnerGET = ""
                outputPOST = ""
                cpus = 1
                mem = 1
        
        def loadEndpoints(self):
                # Load the configuration values from file
                f = open('config.txt')
                lines = f.readlines()
                f.close()
                for line in lines:
                        if line.startswith('JobRunner_GET '):
                                jobrunnerGET = line.split(' ')[1].strip()
                                print('JobRunner POST endpoint set to ' + jobrunnerGET)
                        if line.startswith('Output_POST '):
                                outputPOST = line.split(' ')[1].strip()
                                print('Output POST endpoint set to ' + outputPOST)

        def getJob(self):
                r = requests.get(self.jobrunnerGET)
                # Check for good HTTP response
                if r.status_code == 200:
                        # Check for logically error in response
                        if not "errorMessage" in r.text:
                                print("Good response: " + str(r.text))
                        else:
                                # logic error
                                print("Error from web service:\n" + str(r.text))
                else:
                        # HTTP error
                        print("HTTP error: " + str(r.status_code))

        def getSystemSpecs(self):
                cpus = psutil.cpu_count()
                print('Number of cores set to ' + str(cpus))
                os.environ["OMP_NUM_THREADS"] = str(cpus)
                os.environ["MKL_NUM_THREADS"] = str(cpus)
                myoutput = open('env.out', 'w')
                p = subprocess.Popen("env", stdout=myoutput)
                p.wait()
                myoutput.flush()
                myoutput.close()
                mem = psutil.virtual_memory().available
                print('Bytes of available memory ' + str(mem))

        def runPsi4(self):
                return ResultCode.success

        def uploadResults(self):
                pass

        # Main
        def runOnce(self):
                self.loadEndpoints()
                self.getJob()
                self.getSystemSpecs()
                result = self.runPsi4()
                if result == ResultCode.success:
                        self.uploadResults()

                #   Check exit code
                #   Upload results
                #   Clear scratch

                return ResultCode.success


