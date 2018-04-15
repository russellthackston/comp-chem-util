#!/bin/bash
echo "userdata.sh script launched..."
curl -o ec2-myriad.sh https://s3.amazonaws.com/psi4share/ec2-myriad.sh
mv ec2-myriad.sh /home/ec2-user/ec2-myriad.sh
chmod +rx /home/ec2-user/ec2-myriad.sh
echo "Launching ec2-myriad.sh as ec2-user..."
su -c /home/ec2-user/ec2-myriad.sh - ec2-user
echo "Finished ec2-myriad.sh"
