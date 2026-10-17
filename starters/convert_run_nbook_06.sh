#!/bin/bash

# Load the Python module
module load python3

# Step 1: Convert Jupyter notebooks to Python scripts
echo "Converting notebooks to scripts..."
# start is in /runner folder
cd .. # to project home
cd nbooks 
jupyter nbconvert --to script 06_EDA_OBS_Data.ipynb

# Step 2: Move Python scripts to the 'scripts' folder (assumed to exist)
echo "Moving scripts to the scripts directory..."
mv 06_EDA_OBS_Data.py ../runner_scripts/

# Step 3: Navigate to the 'scripts' folder
cd ../runner_scripts

# Step 4: Make the Python scripts executable
echo "Making Python scripts executable..."
chmod 744 06_EDA_OBS_Data.py


# Step 7: Navigate to the 'runner' folder and submit jobs to SLURM

cd ../runner
chmod +x runner_06.sh

# Submit Q1, each waiting for the previous to finish
job_id_Q1=$(sbatch --parsable runner_06.sh ../runner_scripts/EDA_timestamps_Q1_Jan-Mar.lst)
echo "Submitted Q1 with Job ID: $job_id_Q1"

job_id_Q2=$(sbatch --parsable --dependency=afterany:$job_id_Q1 runner_06.sh ../runner_scripts/EDA_timestamps_Q2_Apr-Jun.lst)
echo "Submitted Q2 with Job ID: $job_id_Q2"

job_id_Q3=$(sbatch --parsable --dependency=afterany:$job_id_Q2 runner_06.sh ../runner_scripts/EDA_timestamps_Q3_Jul-Sep.lst)
echo "Submitted Q3 with Job ID: $job_id_Q3"

job_id_Q4=$(sbatch --parsable --dependency=afterany:$job_id_Q3 runner_06.sh ../runner_scripts/EDA_timestamps_Q4_Oct-Dec.lst)
echo "Submitted Q4 with Job ID: $job_id_Q4"

echo "All quarters submitted. Q2 waits for Q1, Q3 waits for Q2, Q4 waits for Q3."

# # Submit the first job for processing daily data
# echo "Submitting runner_06.sh to SLURM with dates_06.lst..."
# job_id_06=$(sbatch --parsable runner_06.sh ../runner_scripts/timeperiods_EDA.lst)

# echo "Submitted runner_06.sh with Job ID: $job_id_06"

# # Step 8: Wait for runner_10.sh to complete
# echo "Waiting for runner_06.sh (Job ID: $job_id_06) to complete..."

# # Use a loop to check job status
# while true; do
#     # Check if the job is still running or in the queue
#     job_status=$(squeue --job $job_id_06)

#     if [[ -z "$job_status" ]]; then
#         # Job is not in the queue, meaning it has completed
#         echo "runner_06.sh has completed."
#         break
#     else
#         # Job is still running or in queue, wait and check again
#         echo "runner_06.sh is still running. Checking again in 5 minutes..."
#         sleep 300
#     fi
# done


