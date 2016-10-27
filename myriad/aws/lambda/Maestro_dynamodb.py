import boto3
import json
import sys
import logging
import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
This function adds a new job to the database.
The job consists of some meta data and the specific job definition 
(example: 'Displacements' in the form "-1,-1,-2")
This function is NOT publicly available via API Gateway.
{
  "JobGroup": "NS2",
  "JobCategory": "5Z",
  "JobName": "NS2-5Z-1",
  "JobDefinition": {"Displacements":"-1,-1,-2"},
  "Created": "2016-07-17 15:26:45"
}
'''
def add_job(event, context):
	dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

	pending = dynamodb.Table('MaestroPendingJobs')
	try:
		item = event
		jobID = str(uuid.uuid4())
		item['JobID'] = jobID
		response = pending.put_item(Item=item)
	except ClientError as e:
		logger.info(e)
		raise Exception('500: Database error')
	else:
		return item


'''
This function returns the next available job from the database, if one exists.
The job consists of some meta data and the specific job definition 
(example: 'Displacements' in the form "-1,-1,-2")
This function is publicly available via API Gateway.
{
  "JobID": "12345",
  "JobGroup": "NS2",
  "JobCategory": "5Z",
  "JobName": "NS2-5Z-1",
  "JobDefinition": {"Displacements":"-1,-1,-2"},
  "Created": "2016-07-17 15:26:45"
}
'''
def get_next_job(event, context):
	logger.info(str(event))
	dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

	pending = dynamodb.Table('MaestroPendingJobs')
	executing = dynamodb.Table('MaestroExecutingJobs')
	jobGroup = None
	jobCategory = None
	if 'jobGroup' in event:
		if event['jobGroup'] != "":
			jobGroup = event['jobGroup']
			logger.info("JobGoup set to " + jobGroup)
	if 'jobCategory' in event:
		if event['jobCategory'] != "":
			jobCategory = event['jobCategory']
			logger.info("JobCategory set to " + jobCategory)

	try:
		fe = None
		if jobGroup != None and jobCategory != None:
			fe = Attr('JobGroup').eq(jobGroup) & Attr('JobCategory').eq(jobCategory)
		elif jobGroup != None and jobCategory == None:
			fe = Attr('JobGroup').eq(jobGroup)
		elif jobGroup == None and jobCategory != None:
			fe = Attr('JobCategory').eq(jobCategory)
		if fe != None:
			logger.info(str(fe))
			response = pending.scan(
				FilterExpression=fe
			)
		else:
			response = pending.scan(
				Limit=1
			)

	except ClientError as e:
		logger.info(e)
		raise Exception('500: Database error')
	else:
		if len(response["Items"]) > 0:
			item=response['Items'][0]
			if 'readonly' not in event or event['readonly'] == '':
				executionID = uuid.uuid4()
				logger.info(executionID)
				item['ExecutionID'] = str(executionID)
				now = datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S')
				item['ExecutionRecordCreated'] = now
				# Move the job to the 'executing jobs' table
				response = executing.put_item(Item=item)
				logger.info(response)
				response = pending.delete_item(
					Key={"JobID": item['JobID']}
				)
				logger.info(response)
			return item
		else:
			raise Exception('404: No jobs found')


'''
This function updates the database with the current job status and date/time.
Failed jobs can be manually deleted or otherwise addressed.
This function is not directly available to Myriad via the API Gateway.
It is invoked by the Maestro.dequeue_job_status_results() function.
{
	"source-ip" : "127.0.0.1",
	"body" : {
		"ExecutionID" : "d107a9b9-5fb7-4559-b94d-78c2be148fde",
		"Status" : "Executing",
		"LastUpdate" : "2016-07-17 15:26:45"
	}
}
'''
def post_job_status(event, context):
	dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

	jobStatus = dynamodb.Table('MaestroJobStatus')

	logger.info(str(event))
	machineID = str(event['source-ip'])[:15]

	body = event['body']
	job = body['job']
	executionID = str(job['ExecutionID'])
	status = str(body['Status'])
	lastUpdate = str(body['LastUpdate'])
	if 'Message' in body:
		message = str(body['Message'])
	else:
		message = None
	logger.info(machineID)
	logger.info(executionID)
	logger.info(status)
	logger.info(lastUpdate)
	logger.info(job)
	updated = False
	
	try:
		response = jobStatus.update_item(
			Key={
				'ExecutionID': executionID
			},
			UpdateExpression="set machineID = :mac, jobStatus = :stat, lastUpdate = :last, message = :msg, job = :job",
			ExpressionAttributeValues={
				':mac' : machineID,
				':stat': status,
				':last': lastUpdate,
				':msg' : message,
				':job' : job
			},
			ReturnValues="UPDATED_NEW"
		)
	

	except ClientError as e:
		logger.info(e)
		raise Exception('500: Database error')
		#raise Exception('404: Execution record not found')
	else:
		return "Execution record updated"

'''
This function writes a JobResults record to the database. Called by dequeue_job_results().
This function is not directly available to Myriad via the API Gateway.
It is invoked by the Maestro.dequeue_job_status_results() function.
{
	"source-ip" : "127.0.0.1",
	"body" : {
		"JobID" : "12345",
		"ExecutionID" : "67890",
		"JobResults" : { "FinalEnergy" : "-850.1230942932970000" },
		"Completed" : "2016-10-20 02:34:56"
	}
}
'''
def post_job_results(event, context):
	dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

	jobResultsTable = dynamodb.Table('MaestroJobResults')
	executing = dynamodb.Table('MaestroExecutingJobs')
	jobStatus = dynamodb.Table('MaestroJobStatus')

	# Get the source ip address
	if 'source-ip' not in event:
		raise Exception('400: Missing client IP address')
	machineID = str(event['source-ip'])[:15]
	if machineID == '':
		raise Exception('400: Missing client IP address')

	body = event['body']
	# Get Job GUID
	if 'JobID' not in body:
		raise Exception('400: Missing job ID')
	jobID = body['JobID']
	if jobID == '':
		raise Exception('400: Missing job ID')

	# Get the calculation result
	if 'JobResults' not in body:
		raise Exception('400: Missing job results')
	jobResults = body['JobResults']
	if jobResults == '':
		raise Exception('400: Missing job results')

	# Get the job completion date/time
	if 'Completed' not in body:
		raise Exception('400: Missing completion date/time')
	completed = body['Completed']
	if completed == '':
		raise Exception('400: Missing completion date/time')

	logger.info(body)
	
	job = body['job']
	logger.info(job)

	try:
		response = jobResultsTable.update_item(
			Key={
				'JobID': jobID
			},
			UpdateExpression="set JobResults = :res, SourceIP = :ip, Completed = :comp, job = :job",
			ExpressionAttributeValues={
				':res' : jobResults,
				':ip': machineID,
				':comp' : completed,
				':job' : job
			},
			ReturnValues="UPDATED_NEW"
		)
		response = executing.delete_item(
			Key={"ExecutionID": job['ExecutionID']}
		)
		response = jobStatus.delete_item(
			Key={"ExecutionID": job['ExecutionID']}
		)

	
	except ClientError as e:
		logger.info(e)
		raise Exception('500: Database error')
		#raise Exception('404: Execution record not found')
	else:
		return "Execution record updated"


'''
This function adds a job status update record to the SQS queue for ansynchronous processing.
It is publicly available to Myriad via the API gateway.
'''
def queue_job_status(event, context):
	# Get Job GUID
	if 'JobID' not in event:
		raise Exception('400: Missing job ID')
	jobGUID = event['jobGUID']
	if jobGUID == '':
		raise Exception('400: Missing job ID')

	# Get the output file contents
	if 'Status' not in event:
		raise Exception('400: Missing status')
	status = event['status']
	if status == '':
		raise Exception('400: Missing status')

	# Get the last update date/time
	if 'LastUpdate' not in event:
		raise Exception('400: Missing lastUpdate')
	lastUpdate = event['lastUpdate']
	if lastUpdate == '':
		raise Exception('400: Missing lastUpdate')

	# Get the client IP address
	source_ip = event['source_ip']

	logger.info("Method 'queue_job_status' invoked")
	sqs = boto3.resource('sqs')
	logger.info("Obtained SQS reference from boto3. Getting the queue")
	queue = sqs.get_queue_by_name(QueueName='MaestroSQSQueue')
	logger.info("Queue retrieved. Sending message")
	if 'Message' in event:
		msg = json.dumps({ "jobGUID" : jobGUID, "status" : status, "source_ip" : source_ip, "lastUpdate" : lastUpdate, "message" : event['Message'] })
	else:
		msg = json.dumps({ "jobGUID" : jobGUID, "status" : status, "source_ip" : source_ip, "lastUpdate" : lastUpdate })
	logger.info(msg)
	response = queue.send_message(MessageBody=msg)
	
	# jobResults, source_ip, jobGUID, lastUpdate
	return "Success"

'''
This function adds a job result record to the SQS queue for ansynchronous processing.
It is publicly available to Myriad via the API gateway.
{
    "executionID" : "12345",
    "jobResults" : "Success",
    "completed" : "2016-10-12 01:23:56",
    "source_ip" : "127.0.0.1"
}
'''
def queue_job_results(event, context):
	# Get Job GUID
	if 'executionID' not in event:
		raise Exception('400: Missing execution ID')
	executionID = event['executionID']
	if executionID == '':
		raise Exception('400: Missing execution ID')

	# Get the output file contents
	if 'jobResults' not in event:
		raise Exception('400: Missing job results')
	jobResults = event['jobResults']
	if jobResults == '':
		raise Exception('400: Missing job results')

	# Get the output file contents
	if 'completed' not in event:
		raise Exception('400: Missing completion date/time')
	completed = event['completed']
	if completed == '':
		raise Exception('400: Missing completion date/time')

	# Get the client IP address
	source_ip = event['source_ip']

	logger.info("Method 'queue_job_results' invoked")
	sqs = boto3.resource('sqs')
	logger.info("Obtained SQS reference from boto3. Getting the queue")
	queue = sqs.get_queue_by_name(QueueName='MaestroSQSQueue')
	logger.info("Queue retrieved. Sending message")
	msg = json.dumps({ "executionID" : executionID, "jobResults" : jobResults, "source_ip" : source_ip, "completed" : completed })
	logger.info(msg)
	response = queue.send_message(MessageBody=msg)
	
	# jobResults, source_ip, jobGUID
	return "Success"

'''
This function polls the SQS queue for a message and posts it to the proper 
Lambda function to commit it to the database.
This function is not directly available to Myriad via the API Gateway.
It is invoked via a scheduler.
'''
def dequeue_job_status_results(event, context):
	logger.info("AsyncOutput.write invoked")

	logger.info("Getting reference to sqs from boto3")
	sqs = boto3.resource('sqs')
	logger.info("Getting reference to queue from sqs")
	queue = sqs.get_queue_by_name(QueueName='MaestroSQSQueue')
	logger.info("Obtained queue")
	
	logger.info("Getting a reference to lambda from boto3")
	lambda_client = boto3.client('lambda')
	
	messages = queue.receive_messages(MaxNumberOfMessages=10)
	
	while messages is not None and len(messages) > 0:
		for message in messages:
			logger.info("Processing message: " + message.body)

			'''
			# {'JobID': 'c6769a95-968e-4ce1-8567-6a9202b3c9e8', 
				'Completed': '2016-10-24 19:25:27', 
				'JobResults': '-94.822753307632', 
				'job': {
					'Created': '2016-10-24 02:32:14', 
					'JobDefinition': {
						'Displacements': '0,0,0,0,0,0,0,-3,-1,0,0,0'}, 
						'ExecutionID': 'aa9377ea-96a4-42df-b177-6106fca951ce', 
						'JobGroup': 'CH2NH2', 
						'JobID': 'c6769a95-968e-4ce1-8567-6a9202b3c9e8', 
						'ExecutionRecordCreated': '2016-10-24 07:19:40', 
						'JobName': 'CH2NH2-TZ-202', 
						'JobCategory': 'TZ'
				}
			}
			# {'JobID': 'c6769a95-968e-4ce1-8567-6a9202b3c9e8', 
				'Message': 'Running', 
				'job': {
					'Created': '2016-10-24 02:32:14', 
					'JobDefinition': {
						'Displacements': '0,0,0,0,0,0,0,-3,-1,0,0,0'
					}, 
					'ExecutionID': 'aa9377ea-96a4-42df-b177-6106fca951ce', 
					'JobGroup': 'CH2NH2', 
					'JobID': 'c6769a95-968e-4ce1-8567-6a9202b3c9e8', 
					'ExecutionRecordCreated': '2016-10-24 07:19:40', 
					'JobName': 'CH2NH2-TZ-202', 
					'JobCategory': 'TZ'
				}, 
				'LastUpdate': '2016-10-24 19:24:41', 
				'Status': 'Success'
			}
			'''

			msg = json.loads(message.body)
			logger.info(str(msg))

			if 'JobResults' in msg:
				functionName = "MaestroPostJobResults_DDB"
			elif 'Status' in msg:
				functionName = "MaestroPostJobStatus_DDB"

			logger.info("Calling database Lambda function " + functionName)
			response = lambda_client.invoke(FunctionName=functionName,
				InvocationType='Event',
				Payload=json.dumps(msg))

			logger.info("Response: " + str(response))
		
			if int(response['StatusCode']) >= 200 and int(response['StatusCode']) < 300:
				logger.info("Success response from database Lambda function. Deleting message from SQS queue")
				message.delete()
			elif 'status' in msg:
				# Ignore errors from posting status
				logger.info("Call to write to database Lambda 'Status' function failed. Deleting anyway.")
				message.delete()
			else: 
				logger.info("Call to write to database Lambda function failed. Job results. Keeping message for retry.")
		messages = queue.receive_messages(MaxNumberOfMessages=10)

def create_jobs(event, context):
	s3_client = boto3.client('s3')
	logger.info(event)
	for record in event['Records']:
		bucket = record['s3']['bucket']['name']
		#logger.info(bucket)
		key = record['s3']['object']['key']
		download_path = '/tmp/{}{}'.format(uuid.uuid4(), key.replace('/','-'))
		s3_client.download_file(bucket, key, download_path)
		f = open(download_path)
		lines = f.readlines()
		f.close()
		logger.info(key)
		keys = key.split("/")
		logger.info(keys)
		filename = keys[-1]
		filename = filename.split(".")
		logger.info(filename)
		jobGroup = filename[0]
		logger.info(jobGroup)
		jobCategory = filename[1]
		logger.info(jobCategory)
		processCreateJobsRecord(jobGroup,jobCategory,lines)

'''
{
  "Created": "2016-07-17 15:26:45",
  "ExecutionID": "fac9cf83-dd9c-44f1-b687-4765e024a35b",
  "JobCategory": "5Z",
  "JobDefinition": {
    "Displacements": "-1,-1,-2"
  },
  "JobGroup": "NS2",
  "JobID": "d107a9b9-5fb7-4559-b94d-78c2be148fde",
  "JobName": "NS2-5Z-1"
}
'''
def processCreateJobsRecord(jobGroup,jobCategory,lines):
	dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
	pending = dynamodb.Table('MaestroPendingJobs')
	logger.info("Group: " + jobGroup + ", Category: " + jobCategory)
	i = 1
	now = datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S')
	for l in lines:
		name = jobGroup + "-" + jobCategory + "-" + str(i)
		pending.put_item(Item={
			'Created': now,
			'JobCategory': jobCategory,
			'JobDefinition': {"Displacements": l.strip()},
			'JobGroup': jobGroup,
			'JobID': str(uuid.uuid4()),
			'JobName': name
		})
		i+=1
		if i%1000 == 0:
		       logger.info("Records written: " + str(i))
	logger.info("Processing complete.")

'''
This function returns the next available job from the database, if one exists.
The job consists of some meta data and the specific job definition 
(example: 'Displacements' in the form "-1,-1,-2")
This function is publicly available via API Gateway.
{
  "JobID": "12345",
  "JobGroup": "NS2",
  "JobCategory": "5Z",
  "JobName": "NS2-5Z-1",
  "JobDefinition": {"Displacements":"-1,-1,-2"},
  "Created": "2016-07-17 15:26:45"
}
'''
def get_job_count(event, context):
	dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

	tables = []
	result = {}
	if 'type' in event:
		if event['type'] == 'pending':
			tables = [dynamodb.Table('MaestroPendingJobs')]
		if event['type'] == 'executing':
			tables = [dynamodb.Table('MaestroExecutingJobs')]
		if event['type'] == 'results':
			tables = [dynamodb.Table('MaestroJobResults')]
	else:
		tables = [dynamodb.Table('MaestroPendingJobs'), dynamodb.Table('MaestroExecutingJobs'), dynamodb.Table('MaestroJobResults')]

	total = 0
	for tbl in tables:
		try:
			lastEvaluatedKey = None
			count = 0
			while True:
				if lastEvaluatedKey == None:
					response = tbl.scan(
						Select='COUNT'
					)
					logger.info(response)
				else:
					response = tbl.scan(
						Select='COUNT',
						ExclusiveStartKey=lastEvaluatedKey
					)
				count += response['Count']
				if 'LastEvaluatedKey' in response:
					lastEvaluatedKey = response['LastEvaluatedKey']
				else:
					break

		except ClientError as e:
			logger.info(e)
			raise Exception('500: Database error')
		else:
			total += count
			result[tbl.table_name] = count
	result['Total'] = total
	return result

'''
This function moves a job from table A to table B.
'''
def move_job(event, context):
	dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

	# Set up the scan/delete filters/attributes
	if event['from'] == 'pending':
		fromTable = dynamodb.Table('MaestroPendingJobs')
		kce=Key('JobID').eq(event['id'])
		k={"JobID": event['id']}
	elif event['from'] == 'executing':
		fromTable = dynamodb.Table('MaestroExecutingJobs')
		kce=Key('ExecutionID').eq(event['id'])
		k={"ExecutionID": event['id']}
	elif event['from'] == 'results':
		fromTable = dynamodb.Table('MaestroJobResults')
		kce=Key('JobID').eq(event['id'])
		k={"JobID": event['id']}

	# get the job form the source table source
	response = fromTable.query(KeyConditionExpression=kce)

	# pull out the actual job object from the response
	if event['from'] == 'pending':
		job = response['Items'][0]
	elif event['from'] == 'executing':
		job = response['Items'][0]
	elif event['from'] == 'results':
		job = response['Items'][0]['job']

	# Remove ExecutionID and ExecutionRecordCreated from job
	if 'ExecutionID' in job:
		del job['ExecutionID']
	if 'ExecutionRecordCreated' in job:
		del job['ExecutionRecordCreated']

	# Set up the "to" table and optionally add execution values
	if event['to'] == 'pending':
		toTable = dynamodb.Table('MaestroPendingJobs')
	elif event['to'] == 'executing':
		toTable = dynamodb.Table('MaestroExecutingJobs')
		# Add ExecutionID and ExecutionRecordCreated with new values
		executionID = uuid.uuid4()
		logger.info(executionID)
		job['ExecutionID'] = str(executionID)
		now = datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S')
		job['ExecutionRecordCreated'] = now

	# put the job in the destination table
	toTable.put_item(Item=job)

	# remove the item form the "from" table
	response = fromTable.delete_item(
		Key=k
	)


