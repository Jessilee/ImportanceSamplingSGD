#!/bin/bash

#PBS -l nodes=1:gpus=2
#PBS -l walltime=0:05:00
#PBS -A jvb-000-ag
#PBS -m bea

# Use msub on helios1 to submit this.

# Note that the range above includes both the first and last number.
# The %3 sign after is to instruct the scheduler that we want to run
# as much as %3 simultaneous jobs. For our uses, there isn't much
# of a reason to launch anything less since we're not dealing
# with sequential and independent jobs.


# Before running this, check out a copy of ImportanceSamplingSGD locally.
# Not sure why again, but it works for the HTTP address and not the SSH address.
# git clone https://github.com/alexmlamb/ImportanceSamplingSGD.git ImportanceSamplingSGD

export IMPORTANCE_SAMPLING_SGD_ROOT=${HOME}/Documents/ImportanceSamplingSGD
export PYTHONPATH=${PYTHONPATH}:${IMPORTANCE_SAMPLING_SGD_ROOT}
export IMPORTANCE_SAMPLING_SGD_BIN=${IMPORTANCE_SAMPLING_SGD_ROOT}/integration_distributed_training/bin

export CONFIG_FILE=${IMPORTANCE_SAMPLING_SGD_ROOT}/integration_distributed_training/config_files/helios/02_together/config_000.py

# The config file will contain other information such as the directory in
# which we want to output logs.

# Put garbage in there. It's important that this be a unique file that can
# be reached by all the tasks launched since it's going to be how they
# communicate between themselves initially to share where the database is running,
# what port it's on and what's the password.
export BOOTSTRAP_FILE=${IMPORTANCE_SAMPLING_SGD_ROOT}/bootstrap_019439

# The whole stdbuf is not necessary, but I left it there because it fixes
# some of the strange behavior when we try to redirect the output to a file.


stdbuf -i0 -o0 -e0 python ${IMPORTANCE_SAMPLING_SGD_BIN}/run_database.py --config_file=${CONFIG_FILE} --bootstrap_file=${BOOTSTRAP_FILE} &

THEANO_FLAGS=device=gpu0,floatX=float32 stdbuf -i0 -o0 -e0 python ${IMPORTANCE_SAMPLING_SGD_BIN}/run_master.py --config_file=${CONFIG_FILE} --bootstrap_file=${BOOTSTRAP_FILE} &
THEANO_FLAGS=device=gpu1,floatX=float32 stdbuf -i0 -o0 -e0 python ${IMPORTANCE_SAMPLING_SGD_BIN}/run_worker.py --config_file=${CONFIG_FILE} --bootstrap_file=${BOOTSTRAP_FILE} &

sleep 300