from libmyriad import ResultCode
import requests
import multiprocessing

class Myriad:
        config = []
        jobrunnerPOST = ""
        outputPOST = ""
        cpus = 1
        
        def __init__(self):
                config = []

        # Main
        def runOnce(self):
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
                
                # Load number of cores from file
                #f = open('cpus.txt')
                #cpus = int(f.readline().strip())
                cpus = multiprocessing.cpu_count()
                #f.close()
                print('Number of cores set to ' + str(cpus))

                #   Get system specs
                #   Configure psi4
                #   Run psi4
                #   Check exit code
                #   Upload results
                #   Clear scratch

                return ResultCode.success


