import json
import sys

'''
{
  "Code" : "Success",
  "LastUpdated" : "2016-10-27T22:55:43Z",
  "Type" : "AWS-HMAC",
  "AccessKeyId" : "ABC",
  "SecretAccessKey" : "def",
  "Token" : "VeryLongValue=",
  "Expiration" : "2016-10-28T05:11:17Z"
}

[default]
aws_access_key_id = ABC
aws_secret_access_key = def
region = us-east-1
'''

lines = ""
for line in sys.stdin:
	stripped = line.strip()
	if not stripped: break
	lines += stripped
input = json.loads(lines)
print("[default]")
print("aws_access_key_id = " + str(input['AccessKeyId']))
print("aws_secret_access_key = " + str(input['SecretAccessKey']))
print("region = " + str(sys.argv[1]))
print("")


