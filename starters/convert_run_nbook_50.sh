#!/bin/bash

# Load the Python module
module load python3

# Step 1: Convert Jupyter notebooks to Python scripts
echo "Converting notebooks to scripts..."
# start is in /runner folder
cd .. # to project home
cd nbooks 
jupyter nbconvert --to script 50_add_tas_to_ICON.ipynb

# Step 2: Move Python scripts to the 'scripts' folder (assumed to exist)
echo "Moving scripts to the scripts directory..."
mv 50_add_tas_to_ICON.py ../runner_scripts/

# Step 3: Navigate to the 'scripts' folder
cd ../runner_scripts

# Step 4: Make the Python scripts executable
echo "Making Python scripts executable..."
chmod 744 50_add_tas_to_ICON.py


# Step 7: Navigate to the 'runner' folder and submit jobs to SLURM

cd ../runner
chmod +x runner_50.sh


echo "Submitting runner_50.sh to SLURM jobarray all_nextgems_dates.lst..."
job_id_10=$(sbatch --parsable --array=0-9 runner_50.sh ./all_nextgems_dates/all_nextgems_dates.lst)


echo "Submitted runner_50.sh with Job ID: $job_id_10"


