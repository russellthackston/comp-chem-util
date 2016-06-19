from libmyriad import ResultCode
import requests
import multiprocessing
import psutil
import os
import subprocess

class Myriad:
        
        def __init__(self):
                self.config = []
                self.jobrunnerGET = ""
                self.outputPOST = ""
                self.cpus = 1
                self.mem = 1
        
        def loadEndpoints(self):
                # Load the configuration values from file
                f = open('config.txt')
                lines = f.readlines()
                f.close()
                for line in lines:
                        if line.startswith('JobRunner_GET '):
                                self.jobrunnerGET = line.split(' ')[1].strip()
                                print('JobRunner GET endpoint set to ' + self.jobrunnerGET)
                        if line.startswith('Output_POST '):
                                self.outputPOST = line.split(' ')[1].strip()
                                print('Output POST endpoint set to ' + self.outputPOST)

        def getJob(self):
                print("Requesting a new job from " + str(self.jobrunnerGET))
                r = requests.get(self.jobrunnerGET)
                # Check for good HTTP response
                if r.status_code == 200:
                        # Check for logical error in response
                        if not "errorMessage" in r.text:
                                print("Good response: " + str(r.text))
                                self.parseJob(r.text)
                        else:
                                # logic error
                                print("Error from web service:\n" + str(r.text))
                else:
                        # HTTP error
                        print("HTTP error: " + str(r.status_code))

        def parseJob(self, job):
                # Should look like this...
                #    # JobID: 527
                #    # JobGUID: b4af8ced-3661-11e6-a162-12fe8751cda9
                #    # MakeInputDatParameters: -t MTc
                #    -1,1,-2
                print("Parsing job")
                print(job)

        def getSystemSpecs(self):
                self.cpus = psutil.cpu_count()
                print('Number of cores set to ' + str(self.cpus))
                os.environ["OMP_NUM_THREADS"] = str(self.cpus)
                os.environ["MKL_NUM_THREADS"] = str(self.cpus)
                myoutput = open('env.out', 'w')
                p = subprocess.Popen("env", stdout=myoutput)
                p.wait()
                myoutput.flush()
                myoutput.close()
                self.mem = psutil.virtual_memory().available
                print('Bytes of available memory ' + str(self.mem))

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


