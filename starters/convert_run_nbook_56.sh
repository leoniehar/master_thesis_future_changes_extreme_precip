#!/bin/bash

# Load the Python module
module load python3

# Step 1: Convert Jupyter notebooks to Python scripts
echo "Converting notebooks to scripts..."
# start is in /runner folder
cd .. # to project home
cd nbooks 
jupyter nbconvert --to script 56_calc_month_rainamountfrom_OBS.ipynb

# Step 2: Move Python scripts to the 'scripts' folder (assumed to exist)
echo "Moving scripts to the scripts directory..."
mv 56_calc_month_rainamountfrom_OBS.py ../runner_scripts/

# Step 3: Navigate to the 'scripts' folder
cd ../runner_scripts

# Step 4: Make the Python scripts executable
echo "Making Python scripts executable..."
chmod 744 56_calc_month_rainamountfrom_OBS.py


# Step 7: Navigate to the 'runner' folder and submit jobs to SLURM

cd ../runner
chmod +x runner_56.sh

# Submit Q1, each waiting for the previous to finish
job_id_Q1=$(sbatch --parsable runner_56.sh ../runner_scripts/timestamps_june_2023.lst)
echo "Submitted runner_56 with Job ID: $job_id_Q1"


# Submit Q1, each waiting for the previous to finish
job_id_Q2=$(sbatch --parsable runner_56.sh ../runner_scripts/timestamps_december_2023.lst)
echo "Submitted runner_56 with Job ID: $job_id_Q2"

