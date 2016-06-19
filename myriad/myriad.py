from libmyriad import ResultCode
import requests

class Myriad:
        config = []
        
        def __init__(self):
                config = []

        # Function: Load configuration from config.txt
        def loadConfig(self):
                f = open('config.txt')
                print(f.readline())

        # Function: Upload results to web service

        # Function: Start psi4 job

        # Main
        def runOnce(self):
                return ResultCode.success

        # loadConfig
        # startJob
        # Loop:
        #   Get system specs
        #   Configure psi4
        #   Run psi4
        #   Check exit code
        #   Upload results
        #   Clear scratch
        #   Start new job

