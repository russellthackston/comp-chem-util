#!/bin/bash
mkdir /home/ec2-user/logs/
echo "userdata.sh script launched..." >> logs/userdata.log 2>&1
cd /home/ec2-user/ >> logs/userdata.log 2>&1
curl -o ec2-user-script-myriad.sh https://s3.amazonaws.com/psi4share/ec2-user-script-myriad.sh >> logs/userdata.log 2>&1
chmod +x ec2-user-script-myriad.sh >> logs/userdata.log 2>&1
echo "Launching ec2-user-script-myriad.sh..." >> logs/userdata.log 2>&1
./ec2-user-script-myriad.sh
echo "Finished ec2-user-script-myriad.sh" >> logs/userdata.log 2>&1
