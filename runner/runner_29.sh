#!/bin/bash
#SBATCH --job-name=runner29
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --exclusive
#SBATCH --time=08:00:00
#SBATCH --mail-type=FAIL,END
#SBATCH --account=bb1376
#SBATCH --output=LOG/ICON_29_apply_my_job.%A_%a.out
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
cmd=./29_apply_tobac_ICON_full.py   


input=$*
lfile=`readlink -f $input`

# job arrays (dual if=> job array, else: normal)
if [ -n "${SLURM_ARRAY_TASK_ID}" ]; then 
    TASK_ID=$(printf "%02d" ${SLURM_ARRAY_TASK_ID})
else
    TASK_ID=""
fi


start_proc_from_list -n 32 -p $cmd $lfile$TASK_ID