from libmyriad import ResultCode
import requests

class Myriad:
        config = []
        
        def __init__(self):
                config = []

        # Main
        def runOnce(self):
                # Load the configuration values from file
                f = open('config.txt')
                lines = f.readlines()
                f.close()
                for line in lines:
                        print(line)
                
                #   Get system specs
                #   Configure psi4
                #   Run psi4
                #   Check exit code
                #   Upload results
                #   Clear scratch

                return ResultCode.success


