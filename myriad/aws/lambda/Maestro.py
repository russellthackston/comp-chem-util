import boto3
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
These functions live outside the Maestro VPC so they may interact with SQS.
'''

'''
This function adds a job status update record to the SQS queue for ansynchronous processing.
It is publicly available to Myriad via the API gateway.
'''
def queue_job_status(event, context):
        # Get Job GUID
        if 'jobGUID' not in event:
                raise Exception('400: Missing job GUID')
        jobGUID = event['jobGUID']
        if jobGUID == '':
                raise Exception('400: Missing job GUID')

        # Get the output file contents
        if 'status' not in event:
                raise Exception('400: Missing status')
        status = event['status']
        if status == '':
                raise Exception('400: Missing status')

        # Get the last update date/time
        if 'lastUpdate' not in event:
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
        msg = json.dumps({ "jobGUID" : jobGUID, "status" : status, "source_ip" : source_ip, "lastUpdate" : lastUpdate })
        logger.info(msg)
        response = queue.send_message(MessageBody=msg)
        
        # jobResults, source_ip, jobGUID, lastUpdate
        return "Success"

'''
This function adds a job result record to the SQS queue for ansynchronous processing.
It is publicly available to Myriad via the API gateway.
'''
def queue_job_results(event, context):
        # Get Job GUID
        if 'jobGUID' not in event:
                raise Exception('400: Missing job GUID')
        jobGUID = event['jobGUID']
        if jobGUID == '':
                raise Exception('400: Missing job GUID')

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
        msg = json.dumps({ "jobGUID" : jobGUID, "jobResults" : jobResults, "source_ip" : source_ip, "completed" : completed })
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
        
        for message in queue.receive_messages(MaxNumberOfMessages=10):
                logger.info("Processing message: " + message.body)

                # {"jobResults": "-850.131671682245", "source_ip": "184.72.213.192", "jobGUID": "28088fab-39bd-11e6-8a19-1285a2525167", "completed": "2016-06-16 22:55:10"}
                # {"status": "Success", "source_ip": "184.72.213.192", "jobGUID": "28088fab-39bd-11e6-8a19-1285a2525167"}
                msg = json.loads(message.body)
                logger.info(str(msg))

                if 'jobResults' in msg:
                        functionName = "MaestroPostJobResults"
                elif 'status' in msg:
                        functionName = "MaestroPostJobStatus"

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
