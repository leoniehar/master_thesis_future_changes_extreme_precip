#!/bin/bash

# Load the Python module
module load python3

# Step 1: Convert Jupyter notebooks to Python scripts
echo "Converting notebooks to scripts..."
# start is in /runner folder
cd .. # to project home
cd nbooks 
jupyter nbconvert --to script 23_tobac_segmentation_inputparameter_OBS.ipynb

# Step 2: Move Python scripts to the 'scripts' folder (assumed to exist)
echo "Moving scripts to the scripts directory..."
mv 23_tobac_segmentation_inputparameter_OBS.py ../runner_scripts/

# Step 3: Navigate to the 'scripts' folder
cd ../runner_scripts

# Step 4: Make the Python scripts executable
echo "Making Python scripts executable..."
chmod 744 23_tobac_segmentation_inputparameter_OBS.py


# Step 7: Navigate to the 'runner' folder and submit jobs to SLURM

cd ../runner
chmod +x runner_23.sh

# Submit the first job for processing daily data
echo "Submitting runner_23.sh to SLURM with timestamps.lst..."
job_id_10=$(sbatch --parsable runner_23.sh timestamps.lst)
echo "Submitted runner_23.sh with Job ID: $job_id_10"

# Step 8: Wait for runner_10.sh to complete
echo "Waiting for runner_23.sh (Job ID: $job_id_10) to complete..."

# Use a loop to check job status
while true; do
    # Check if the job is still running or in the queue
    job_status=$(squeue --job $job_id_10)

    if [[ -z "$job_status" ]]; then
        # Job is not in the queue, meaning it has completed
        echo "runner_23.sh has completed."
        break
    else
        # Job is still running or in queue, wait and check again
        echo "runner_23.sh is still running. Checking again in 1 minute..."
        sleep 60
    fi
done


