#!/bin/bash
echo "userdata.sh script launched..."
mkdir /home/ec2-user/logs/
cd /home/ec2-user/
curl -o ec2-user-script-myriad.sh https://s3.amazonaws.com/psi4share/ec2-user-script-myriad.sh
chmod +x ec2-user-script-myriad.sh
echo "Launching ec2-user-script-myriad.sh..."
./ec2-user-script-myriad.sh
echo "Finished ec2-user-script-myriad.sh"
