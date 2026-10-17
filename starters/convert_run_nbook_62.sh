#!/bin/bash

# Load the Python module
module load python3

# Step 1: Convert Jupyter notebooks to Python scripts
echo "Converting notebooks to scripts..."
# start is in /runner folder
cd .. # to project home
cd nbooks 
jupyter nbconvert --to script 62_ICON_full_create_cell_dataframe_withproperties.ipynb

# Step 2: Move Python scripts to the 'scripts' folder (assumed to exist)
echo "Moving scripts to the scripts directory..."
mv 62_ICON_full_create_cell_dataframe_withproperties.py ../runner_scripts/

# Step 3: Navigate to the 'scripts' folder
cd ../runner_scripts

# Step 4: Make the Python scripts executable
echo "Making Python scripts executable..."
chmod 744 62_ICON_full_create_cell_dataframe_withproperties.py


# Step 7: Navigate to the 'runner' folder and submit jobs to SLURM

cd ../runner
chmod +x runner_62.sh

# submit
echo "Submitting runner_62.sh to SLURM with icon_years.lst..."
job_id_10=$(sbatch --parsable runner_62.sh icon_years.lst)
echo "Submitted runner_62.sh with Job ID: $job_id_10"


