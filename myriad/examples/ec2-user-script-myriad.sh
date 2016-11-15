#!/bin/bash

# Download Myriad
downloadMyriad () {
	curl -o libmyriad.py $MYRIAD_GITHUB/$MYRIAD_VERSION/libmyriad.py &>> logs/myriad.log
	curl -o bootstrap-myriad.py $MYRIAD_GITHUB/$MYRIAD_VERSION/bootstrap-myriad.py &>> logs/myriad.log
	curl -o myriad.py $MYRIAD_GITHUB/$MYRIAD_VERSION/myriad.py &>> logs/myriad.log
}

checkForPause () {
	export EC2_PAUSE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=PAUSE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
        if [ "$EC2_PAUSE" != "null" ]; then
		aws ec2 create-tags --tags Key=Name,Value=Paused --resource $EC2_INSTANCE_ID --region $EC2_REGION
	fi
        while [ "$EC2_PAUSE" != "null" ]; do
        	echo "Myriad is paused. Remove the PAUSE tag from the instance to restart" >> logs/myriad.log 2>&1
                sleep 60
		export EC2_PAUSE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=PAUSE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
        done
}

checkForDie () {
	export EC2_DIE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=DIE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
        # If the die.myriad file exists, shutdown the instance
        if [ "$EC2_DIE" != "null" ]; then
        	shutdown -h 0
                exit 0
        fi
}

checkForShutdown () {
        # If the shutdown.myriad file exists, then a shutdown is imminent (from external forces)
        if [ -f shutdown.myriad ]; then
                exit 0
        fi
}

waitForJobTags () {
	# Wait until this instance has been tagged with a molecule/job to run Myriad
	export MOLECULE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=MOLECULE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
	export SUBGROUP=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=SUBGROUP" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
	while [ "$MOLECULE" == "null" ]; do
		sleep 60
		export MOLECULE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=MOLECULE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
		export SUBGROUP=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=SUBGROUP" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
		echo "Molecule = $MOLECULE" &>> logs/myriad.log
		echo "Sub-group = $SUBGROUP" &>> logs/myriad.log
	done
}

# This script runs as root, but psi4/Intder2005 are installed under ec2-user,
# so do some fiddling here with the environment and path
cd /home/ec2-user
export PATH=/home/ec2-user/intder:/home/ec2-user/miniconda/bin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/aws/bin:/home/ec2-user/.local/bin:/home/ec2-user/bin

# Install jq for json parsing
yum install jq -y

# Determine this instance's availability zone, region, ami-id, IP address
export EC2_AVAIL_ZONE=`curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone`
export EC2_REGION="`echo \"$EC2_AVAIL_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
export EC2_AMI_ID=$(curl http://169.254.169.254/latest/meta-data/ami-id)
export EC2_IP=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)
export EC2_INSTANCE_ID=$(curl http://instance-data/latest/meta-data/instance-id)

# Store off this machine's details for later reference by Myriad
echo $EC2_IP > ip.txt
echo $EC2_REGION > region.txt
echo $EC2_AMI_ID > ami-id.txt
echo $EC2_INSTANCE_ID > instance-id.txt

# Let the world know we're initializing the server
aws ec2 create-tags --tags Key=Name,Value=Initializing --resource $EC2_INSTANCE_ID --region $EC2_REGION

# Endpoint for the Myriad project on GitHub and for my job files on S3
export MYRIAD_GITHUB=https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad
export MYRIAD_VERSION=v1
export MYRIAD_AWS=http://psi4share.s3-website-us-east-1.amazonaws.com

# Go ahead and create the output files for easy use of the tail command
touch logs/myriad.log

# Update all software and packages
echo "Updating software" &>> logs/myriad.log
yum update -y &>> logs/myriad.log
conda update --yes --all &>> logs/myriad.log
python34 -m pip install --upgrade pip &>> logs/myriad.log
python34 -m pip install requests --upgrade &>> logs/myriad.log
python34 -m pip install psutil --upgrade &>> logs/myriad.log

# Decide on the number of attached ephemeral storage disks
# If more than one, join them together as a single logical volume
export SECONDDISK=$(sudo fdisk -l | grep /dev/xvdc | wc -l)

if [ "$SECONDDISK" == "1" ]; then
	# MULTIPLE-INSTANCE-STORES, such as /dev/sdb, /dev/sdc, etc.
	# This scriplet handles up to 25 drives [b-z]
	umount /dev/xvdb &>> logs/myriad.log
	pvcreate /dev/xvd[b-z] --verbose --yes &>> logs/myriad.log
	vgcreate -s 16M vg /dev/xvd[b-z] --verbose &>> logs/myriad.log
	LVSIZE=$(vgs vg --units k | rev | cut -d " " -f1 | rev | xargs)
	LVCOUNT=$(pvdisplay | grep /dev/sd | wc -l)
	lvcreate -L $LVSIZE -n lvg -i$LVCOUNT vg &>> logs/myriad.log
	mkfs.ext3 /dev/vg/lvg &>> logs/myriad.log
	mkdir /mnt/scratch
	mount /dev/vg/lvg /mnt/scratch &>> logs/myriad.log
fi

if [ "$SECONDDISK" == "0" ]; then
	# SINGLE-INSTANCE-STORE, such as /dev/sdb only
	# Setup the scratch space for psi4
	mkfs -t ext3 /dev/sdb &>> logs/myriad.log
	mkdir /mnt/scratch
	mount /dev/sdb /mnt/scratch &>> logs/myriad.log
fi

# Export the scratch space location to the environment
export PSI_SCRATCH=/mnt/scratch

# Let the world know we're ready to run jobs
aws ec2 create-tags --tags Key=Name,Value=Waiting --resource $EC2_INSTANCE_ID --region $EC2_REGION

waitForJobTags

# Begin running jobs
while [ true ]; do

	# Download Myriad config file(s)
	echo "Downloading config.txt..." &>> logs/myriad.log
	URL=$MYRIAD_AWS/$MOLECULE/config.txt
	echo "Accessing $URL" &>> logs/myriad.log
	curl -o config.txt $URL &>> logs/myriad.log

	# This molecule requires an MTS file in the BASIS folder
	# TO DO: Make this option-driven
	URL=$MYRIAD_AWS/$MOLECULE/mt.gbs
	echo "Accessing $URL" &>> logs/myriad.log
	curl -o mt.gbs $URL &>> logs/myriad.log
	mv mt.gbs /home/ec2-user/miniconda/share/psi4/basis/ &>> logs/myriad.log

	# Check for a sub-group of "null" and assume that means no sub-group
	if [ "$SUBGROUP" == "null" ]; then
		downloadMyriad
		echo "Executing Myriad with JobGroup=$MOLECULE" >> logs/myriad.log 2>&1
	        python34 bootstrap-myriad.py --group $MOLECULE --server $MYRIAD_GITHUB --version $MYRIAD_VERSION >> logs/myriad.log 2>&1
	else
		downloadMyriad
		echo "Executing Myriad with JobGroup=$MOLECULE and JobCategory=$SUBGROUP" >> logs/myriad.log 2>&1
	        python34 bootstrap-myriad.py --group $MOLECULE --subGroup $SUBGROUP --server $MYRIAD_GITHUB --version $MYRIAD_VERSION >> logs/myriad.log 2>&1
	fi

	for f in *.zip
	do
		echo "Uploading $f" >> logs/myriad.log 2>&1
		aws s3 cp $f s3://myriaddropbox/
	done

        # when Myriad exits it will go into a loop and wait
        echo "Myriad exit code is $?" >> logs/myriad.log 2>&1

	checkForShutdown
	checkForDie
	checkForPause
	waitForJobTags

done
