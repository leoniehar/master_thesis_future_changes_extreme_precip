#!/bin/bash

# Load the Python module
module load python3

# Step 1: Convert Jupyter notebooks to Python scripts
echo "Converting notebooks to scripts..."
# start is in /runner folder
cd .. # to project home
cd nbooks 
jupyter nbconvert --to script 28_dup_PE_apply_tobac_ICON.ipynb

# Step 2: Move Python scripts to the 'scripts' folder (assumed to exist)
echo "Moving scripts to the scripts directory..."
mv 28_dup_PE_apply_tobac_ICON.py ../runner_scripts/

# Step 3: Navigate to the 'scripts' folder
cd ../runner_scripts

# Step 4: Make the Python scripts executable
echo "Making Python scripts executable..."
chmod 744 28_dup_PE_apply_tobac_ICON.py


# Step 7: Navigate to the 'runner' folder and submit jobs to SLURM

cd ../runner
chmod +x runner_28.sh

# submit
echo "Submitting runner_28.sh to SLURM with timestamps_december_2023.lst..."
job_id_10=$(sbatch --parsable runner_28.sh timestamps_december_2023.lst)
echo "Submitted runner_28.sh with Job ID: $job_id_10"



# Step 8: Wait for both jobs to complete
echo "Waiting for Job IDs $job_id_10 to complete..."
for job_id in $job_id_10; do #$job_id_11; do
    while true; do
        job_status=$(squeue --job $job_id 2>/dev/null | tail -n +2)
        if [[ -z "$job_status" ]]; then
            echo "runner_28.sh with Job $job_id has completed."
            break
        else
            echo "runner_28.sh with Job $job_id is still running. Checking again in 1 minute..."
            sleep 60
        fi
    done
done


# copy log files to output directory
OUTPUT_DIR="../output/apply_seg"   # ./runner/../output/apply → project root

for job_id in $job_id_10; do
    LOG_FILE="LOG/ICON_28_apply_my_job.${job_id}.out"
    if [[ -f "$LOG_FILE" ]]; then
        cp "$LOG_FILE" "$OUTPUT_DIR/28_dup_PE_apply_tobac_ICON.${job_id}.out"
        echo "Log copied to $OUTPUT_DIR/28_dup_PE_apply_tobac_ICON.${job_id}.out"
    else
        echo "WARNING: Log file $LOG_FILE not found."
    fi
done