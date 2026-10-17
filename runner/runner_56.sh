#!/bin/bash
#SBATCH --job-name=runner56
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --exclusive
#SBATCH --time=08:00:00
#SBATCH --mail-type=FAIL
#SBATCH --account=bb1376
#SBATCH --output=LOG/my_job.%j.out
#SBATCH --mem=0

# limit stacksize ... adjust to your programs need
# and core file size
ulimit -s 204800
ulimit -c 0


export PATH=$PATH:/work/bb1262/tools/utils/ # to get start_proc_from_list

module load python3

eval "$(/sw/spack-levante/mambaforge-22.9.0-2-Linux-x86_64-kptncg/bin/conda shell.bash hook)"
conda activate /work/bb1376/user/leonie/conda/envs/MA_numpy23


# location of scripts relative to this runner
cd ../runner_scripts  

# here is the scriptname
cmd=./56_calc_month_rainamountfrom_OBS.py   

lfile=`readlink -f $1`          # pass the list file as argument to the runner
start_proc_from_list -n 16 -p "$cmd" "$lfile"  