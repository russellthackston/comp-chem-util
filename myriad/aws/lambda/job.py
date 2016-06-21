class Job:
    
    def __init__(self, id="", name="", jobDefinition="", created="", makeInputDatParameters="", jobGroup=""):
        self.id = id
        self.name = name
        self.jobDefinition = jobDefinition
        self.created = created
        self.makeInputDatParameters = makeInputDatParameters
        self.jobGroup = jobGroup
