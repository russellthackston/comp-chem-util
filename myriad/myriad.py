from libmyriad import ResultCode
import requests
import multiprocessing
import psutil
import os

class Myriad:
        config = []
        jobrunnerPOST = ""
        outputPOST = ""
        cpus = 1
        mem = 1
        
        def __init__(self):
                config = []
                jobrunnerPOST = ""
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
                                jobrunnerPOST = line.split(' ')[1].strip()
                                print('JobRunner POST endpoint set to ' + jobrunnerPOST)
                        if line.startswith('Output_POST '):
                                outputPOST = line.split(' ')[1].strip()
                                print('Output POST endpoint set to ' + outputPOST)

        def getSystemSpecs(self):
                cpus = psutil.cpu_count()
                print('Number of cores set to ' + str(cpus))
                os.environ["OMP_NUM_THREADS"] = str(cpus)
                os.environ["MKL_NUM_THREADS"] = str(cpus)
                mem = psutil.virtual_memory().available
                print('Bytes of available memory ' + str(mem))

        # Main
        def runOnce(self):
                self.loadEndpoints()
                self.getSystemSpecs()
                

                #   Configure psi4
                #   Run psi4
                #   Check exit code
                #   Upload results
                #   Clear scratch

                return ResultCode.success


