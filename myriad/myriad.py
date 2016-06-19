from libmyriad import ResultCode
import requests

class Myriad:
        config = []
        jobrunnerPOST = ""
        outputPOST = ""
        
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
                                jobrunnerPOST = line.split(' ')[1]
                        if line.startswith('Output_POST '):
                                outputPOST = line.split(' ')[1]
                
                #   Get system specs
                #   Configure psi4
                #   Run psi4
                #   Check exit code
                #   Upload results
                #   Clear scratch

                return ResultCode.success


