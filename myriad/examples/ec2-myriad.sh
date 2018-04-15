#!/bin/bash

export MLOG=$HOME/logs/myriad.log
export PAUSED=0  # pause flag to make sure we don't spam AWS with create-tag operations while paused

# Download Myriad
downloadMyriad () {
	curl -o libmyriad.py $MYRIAD_GITHUB/$MYRIAD_VERSION/libmyriad.py &>> $MLOG
	curl -o bootstrap-myriad.py $MYRIAD_GITHUB/$MYRIAD_VERSION/bootstrap-myriad.py &>> $MLOG
	curl -o myriad.py $MYRIAD_GITHUB/$MYRIAD_VERSION/myriad.py &>> $MLOG
}

checkForPause () {
	export EC2_PAUSE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=PAUSE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
        if [ "$EC2_PAUSE" != "null" ] && [ "$PAUSED" != 1 ]; then
		aws ec2 create-tags --tags Key=Name,Value=Paused --resource $EC2_INSTANCE_ID --region $EC2_REGION
		export PAUSED=1
	fi
        while [ "$EC2_PAUSE" != "null" ]; do
        	echo "Myriad is paused. Remove the PAUSE tag from the instance to restart" >> $MLOG 2>&1
                sleep 60
		export EC2_PAUSE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=PAUSE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
        done
        export PAUSED=0
}

checkForDie () {
	export EC2_DIE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=DIE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
        # If the die.myriad file exists, shutdown the instance
        if [ "$EC2_DIE" != "null" ]; then
		zip $(cat ip.txt)_shutdown.zip logs/*
		uploadZipfiles
        	sudo shutdown -h 0
                exit 0
        fi
}

checkForShutdown () {
        # If the shutdown.myriad file exists, then a shutdown is imminent (from external forces)
        if [ -f shutdown.myriad ]; then
		zip $(cat ip.txt)_shutdown.zip logs/*
		uploadZipfiles
                exit 0
        fi
}

waitForJobTags () {
	echo "Checking for job tags on instance" &>> $MLOG
	# Wait until this instance has been tagged with a molecule/job to run Myriad
	export MOLECULE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=MOLECULE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
	export SUBGROUP=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=SUBGROUP" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
	while [ "$MOLECULE" == "null" ]; do
		echo "No job tags found on instance. Sleeping for 60 seconds..." &>> $MLOG
		sleep 60
		echo "Checking for shutdown/die/pause" &>> $MLOG
		checkForShutdown
		checkForDie
		checkForPause
		export MOLECULE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=MOLECULE" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
		export SUBGROUP=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$EC2_INSTANCE_ID" "Name=key,Values=SUBGROUP" --region $EC2_REGION | jq '.Tags[0].Value' | tr -d '"')
		echo "Molecule = $MOLECULE" &>> $MLOG
		echo "Sub-group = $SUBGROUP" &>> $MLOG
	done
}

uploadZipfiles () {
	for f in *.zip
	do
		echo "Uploading $f" >> $MLOG 2>&1
		aws s3 cp $f s3://myriaddropbox/
		rm -f $f
	done
}

# Work out of the ec2-user home directory
whoami
echo $HOME
cd /home/ec2-user/

# Determine this instance's availability zone, region, ami-id, IP address
export EC2_AVAIL_ZONE=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
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
mkdir -p $HOME/logs/
touch $MLOG

# Create a directory for the scratch files
echo "Creating the scratch folder" &>> $MLOG
sudo mkdir -p /mnt/scratch &>> $MLOG

# Export the scratch space location to the environment
export PSI_SCRATCH=/mnt/scratch
echo "PSI_SCRATCH="$PSI_SCRATCH &>> $MLOG

# Update system software and packages
echo "Updating system software" &>> $MLOG
sudo yum update -y &>> $MLOG
sudo yum install jq -y &>> $MLOG           # Needed for parsing json (above)
sudo yum install gcc -y &>> $MLOG          # Needed for psutils
sudo yum install libgfortran -y &>> $MLOG  # Needed for Intder2005

# Install Python 3
echo "Installing Python 3.4 and development tools" &>> $MLOG
sudo yum install python34 -y &>> $MLOG
sudo yum install python34-devel -y &>> $MLOG

# Download pip and additional Python packages
echo "Downloading pip and tools" &>> $MLOG
curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py &>> $MLOG
sudo python3.4 get-pip.py &>> $MLOG
sudo python3.4 -m pip install requests &>> $MLOG
sudo python3.4 -m pip install psutil &>> $MLOG
sudo python3.4 -m pip install numpy --upgrade &>> $MLOG

# Download and configure Intder2005
mkdir -p $HOME/intder &>> $MLOG
pushd $HOME/intder &>> $MLOG
curl -o Intder2005.f https://s3.amazonaws.com/psi4share/Intder2005.f &>> $MLOG
curl -o Intder2005.x https://s3.amazonaws.com/psi4share/Intder2005.x &>> $MLOG
sudo chmod +x Intder2005.*
popd &>> $MLOG
export PATH=$HOME/intder:$PATH

# Install Psi4conda
echo "Installing Psi4conda" &>> $MLOG
curl -O "http://www.psicode.org/downloads/Psi4conda2-latest-Linux.sh" --keepalive-time 2 &>> $MLOG
bash Psi4conda2-latest-Linux.sh -b -p $HOME/psi4conda &>> $MLOG

# Check for successful installation of psi4
if [ ! -f $HOME/psi4conda/bin/psi4 ]; then
	# Install Psi4conda from a backup copy
	echo "Installation of Psi4conda failed" &>> $MLOG
	echo "Obtaining backup copy..." &>> $MLOG
	curl -O "https://s3.amazonaws.com/psi4share/Psi4conda2-latest-Linux.sh" &>> $MLOG
	bash Psi4conda2-latest-Linux.sh -b -p $HOME/psi4conda &>> $MLOG
	if [ ! -f $HOME/psi4conda/bin/psi4 ]; then
		echo "Installation of backup version of Psi4conda failed" &>> $MLOG
		zip $(cat ip.txt)_psi4_install_failed.zip logs/*
		uploadZipfiles
		sudo shutdown -h 0
		exit 0
	fi
fi
export PATH=$HOME/psi4conda/bin:$PATH
echo "Completed installation of Psi4conda" &>> $MLOG

# Decide on the number of attached ephemeral storage disks
# If more than one, join them together as a single logical volume
export SECONDDISK=$(sudo fdisk -l | grep /dev/xvdc | wc -l)

if [ "$SECONDDISK" == "1" ]; then
	# MULTIPLE-INSTANCE-STORES, such as /dev/sdb, /dev/sdc, etc.
	# This scriplet handles up to 25 drives [b-z]
	sudo umount /dev/xvdb &>> $MLOG
	sudo pvcreate /dev/xvd[b-z] --verbose --yes &>> $MLOG
	sudo vgcreate -s 16M vg /dev/xvd[b-z] --verbose &>> $MLOG
	LVSIZE=$(sudo vgs vg --units k | rev | cut -d " " -f1 | rev | xargs)
	LVCOUNT=$(sudo pvdisplay | grep /dev/sd | wc -l)
	sudo lvcreate -L $LVSIZE -n lvg -i$LVCOUNT vg &>> $MLOG
	sudo mkfs.ext3 /dev/vg/lvg &>> $MLOG
	sudo mount /dev/vg/lvg /mnt/scratch &>> $MLOG
fi

if [ "$SECONDDISK" == "0" ]; then
	# SINGLE-INSTANCE-STORE, such as /dev/sdb only
	# Setup the scratch space for psi4
	sudo mkfs -t ext3 /dev/sdb &>> $MLOG
	sudo mount /dev/sdb /mnt/scratch &>> $MLOG
fi

# Make ec2-user the owner of the scratch folder
sudo chown -R ec2-user:ec2-user /mnt/scratch &>> $MLOG

# Let the world know we're ready to run jobs
aws ec2 create-tags --tags Key=Name,Value=Waiting --resource $EC2_INSTANCE_ID --region $EC2_REGION

waitForJobTags

# Begin running jobs
while [ true ]; do

	# Download Myriad config file(s)
	echo "Downloading config.txt..." &>> $MLOG
	URL=$MYRIAD_AWS/$MOLECULE/config.txt
	echo "Accessing $URL" &>> $MLOG
	curl -o config.txt $URL &>> $MLOG

	# This molecule requires an MTS file in the BASIS folder
	# TO DO: Make this option-driven
	URL=$MYRIAD_AWS/$MOLECULE/mt.gbs
	echo "Accessing $URL" &>> $MLOG
	curl -o mt.gbs $URL &>> $MLOG
	mv mt.gbs $HOME/psi4conda/share/psi4/basis/ &>> $MLOG

	# Check for a sub-group of "null" and assume that means no sub-group
	if [ "$SUBGROUP" == "null" ]; then
		downloadMyriad
		echo "Executing Myriad with JobGroup=$MOLECULE" >> $MLOG 2>&1
	        python3.4 bootstrap-myriad.py --group $MOLECULE --server $MYRIAD_GITHUB --version $MYRIAD_VERSION >> $MLOG 2>&1
	else
		downloadMyriad
		echo "Executing Myriad with JobGroup=$MOLECULE and JobCategory=$SUBGROUP" >> $MLOG 2>&1
	        python3.4 bootstrap-myriad.py --group $MOLECULE --subGroup $SUBGROUP --server $MYRIAD_GITHUB --version $MYRIAD_VERSION >> $MLOG 2>&1
	fi


        # when Myriad exits it will go into a loop and wait
        echo "Myriad exit code is $?" >> $MLOG 2>&1

	checkForShutdown
	checkForDie
	uploadZipfiles
	waitForJobTags

done
