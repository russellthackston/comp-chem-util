#!/bin/bash
# This script runs as root, but psi4/Intder2005 are installed under ec2-user,
# so do some fiddling here with the environment and path
cd /home/ec2-user
export PATH=/home/ec2-user/intder:/home/ec2-user/miniconda/bin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/aws/bin:/home/ec2-user/.local/bin:/home/ec2-user/bin

# Endpoint for the Myriad project on GitHub and for my job files on S3
export MYRIAD_GITHUB=https://raw.githubusercontent.com/russellthackston/comp-chem-util/master/myriad/
export MYRIAD_VERSION=v1
export MYRIAD_AWS=http://psi4share.s3-website-us-east-1.amazonaws.com
export MOLECULE=CH2NH2
export SUBGROUP=TZ

# Go ahead and create the output files for easy use of the tail command
touch startup-myriad.log
touch mm.out
touch myriad.log

# Store off this machine's IP address and instance-id for later reference
curl http://169.254.169.254/latest/meta-data/public-ipv4 > ip.txt
curl http://169.254.169.254/latest/meta-data/ami-id > ami-id.txt

# Download Myriad config file(s)
echo Downloading config.txt... &>> startup-myriad.log
curl -o config.txt $MYRIAD_AWS/$MOLECULE/config.txt &>> startup-myriad.log

# Update all software and packages
echo Updating software &>> startup-myriad.log
yum update -y &>> startup-myriad.log
conda update --yes --all &>> startup-myriad.log
python34 -m pip install --upgrade pip &>> startup-myriad.log
python34 -m pip install requests --upgrade &>> startup-myriad.log
python34 -m pip install psutil --upgrade &>> startup-myriad.log

# Download Myriad
curl -o bootstrap-myriad.py $MYRIAD_GITHUB/$MYRIAD_VERSION/bootstrap-myriad.py &>> startup-myriad.log
curl -o bootstrap-myriad.py $MYRIAD_GITHUB/$MYRIAD_VERSION/libmyriad.py &>> startup-myriad.log
curl -o bootstrap-myriad.py $MYRIAD_GITHUB/$MYRIAD_VERSION/myriad.py &>> startup-myriad.log

# This molecule requires an MTS file in the BASIS folder
curl -o mt.gbs $MYRIAD_AWS/$MOLECULE/mt.gbs &>> startup-myriad.log
mv mt.gbs /home/ec2-user/miniconda/share/psi4/basis/ &>> startup-myriad.log

# Setup the scratch space for psi4
mkfs -t ext3 /dev/sdb &>> startup-myriad.log
mkdir /mnt/scratch
mount /dev/sdb /mnt/scratch &>> startup-myriad.log
export PSI_SCRATCH=/mnt/scratch

# uncomment this line if you want the instance to be self-terminating when the jobs run out
# but don't uncomment the pause.myriad line (below)
#touch die.myriad

# uncomment this line if you want the instance to pause Myriad when the jobs run out
#touch pause.myriad

# sleep for 1-60 seconds, so a group of VMs don't all grab the same first job
sleep $(shuf -i 1-60 -n 1)

# Begin running jobs
while [ true ]; do
        #python34 bootstrap-myriad.py --server $MYRIAD_GITHUB --version $MYRIAD_VERSION >> mm.out 2>&1
        #python34 bootstrap-myriad.py --group $MOLECULE --server $MYRIAD_GITHUB --version $MYRIAD_VERSION >> mm.out 2>&1
        #python34 bootstrap-myriad.py --subGroup $SUBGROUP --server $MYRIAD_GITHUB --version $MYRIAD_VERSION >> mm.out 2>&1
        python34 bootstrap-myriad.py --group $MOLECULE --subGroup $SUBGROUP --server $MYRIAD_GITHUB --version $MYRIAD_VERSION >> mm.out 2>&1
        # when Myriad exits it will go into a loop and wait
        echo "Myriad exit code is $?"
        
        while [ -f pause.myriad ]; do
                # delete the pause.myriad file to restart Myriad
                sleep 10
        done

        # To end Myriad, create a die.myriad or shutdown.myriad file and delete the pause.myriad file 
        if [ -f die.myriad ]; then
                exit 0
        fi
        if [ -f shutdown.myriad ]; then
                exit 0
        fi
done