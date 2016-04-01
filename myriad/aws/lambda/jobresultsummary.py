class JobResultsSummary:

    def __init__(self, jobGUID="", success="", executionDateTime="", scratch="", memory="", memory2="", userTime="", systemTime="", totalTime="", userTime2="", systemTime2="", wallClockTime="", cpuPercent="", exitStatus="", cpus="", freeMem=""):
		self.jobGUID = jobGUID
		self.success = success
		self.executionDateTime = executionDateTime
		self.scratch = scratch
		self.memory = memory
		self.memory = memory2
		self.userTime = userTime
		self.systemTime = systemTime
		self.totalTime = totalTime
		self.userTime2 = userTime2
		self.systemTime2 = systemTime2
		self.wallClockTime = wallClockTime
		self.cpuPercent = cpuPercent
		self.exitStatus = exitStatus
		self.cpus = cpus
		self.freeMem = freeMem

