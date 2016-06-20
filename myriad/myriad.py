from libmyriad import ResultCode
import requests
import multiprocessing
import psutil
import os
import subprocess
import shutil
import datetime

class Myriad:
        
        def __init__(self):
                self.config = []
                self.jobrunnerGET = ""
                self.outputPOST = ""
                self.cpus = 1
                self.mem = 1
                self.displacements = ""
                self.jobID = ""
                self.jobGUID = ""
                self.makeInputDatParameters = ""
                self.jobFolder = ""

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
                                print("Good response:\n" + str(r.text))
                                result = self.parseJob(r.text.split('\n'))
                                if result == ResultCode.success:
                                        f = open('disp.dat', 'w')
                                        f.write(self.displacements)
                                        f.flush()
                                        f.close()
                                return result
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
                                elif "MakeInputDatParameters:" in line.strip():
                                        self.makeInputDatParameters = line.split(':')[1].strip()
                                        print('MakeInputDatParameters set to ' + str(self.makeInputDatParameters))
                                else:
                                        print('Unknown line')
                        else:
                                # Non-blank, non-commented line. Must be the displacements
                                self.displacements = line
                return ResultCode.success

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
                result = p.wait()
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
                pass

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
                import makeInputDatFile
                m = makeInputDatFile.MakeInputDat()
                m.makefile(self.makeInputDatParameters)

        # Main
        def runOnce(self):
                self.loadEndpoints()
                result = ResultCode.success
                if self.getJob() == ResultCode.success:
                        self.getSystemSpecs()
                        self.clearScratch()
                        self.makeJobFolder()
                        self.makeInputDat()
                        result = self.runPsi4()
                        if result == ResultCode.success:
                                self.uploadResults()
                        self.closeJobFolder()
                        self.clearScratch()
                else:
                        result = ResultCode.noaction
                return result
