#!/usr/bin/env python

import subprocess as sub
import argparse
import os

def get_user():
    "Get the current user"
    return sub.Popen(["whoami"], stdout=sub.PIPE).stdout.read().strip()

def get_id():
    "Return all pending job ids for user"
    cmd = ["squeue", "-u", get_user(), "-h", "--format=%i,%t"]
    ids = sub.Popen(cmd, stdout=sub.PIPE).stdout.readlines()
    ids = map(lambda x: x.split(","), ids)
    ids = filter(lambda y: y[1] == "PD", [map(lambda x: x.strip(), line) for line in ids])
    return [x[0] for x in ids]

def get_user_accounts():
    "Return list of all accounts available to user"
    cmd = ["cost", "-u", get_user()]
    output = sub.Popen(cmd, stdout=sub.PIPE).stdout.readlines()
    accounts = filter(lambda x: x.startswith(get_user()), output)
    accounts = [line.split() for line in accounts]
    return map(lambda x: x[1], accounts)

def get_priority(jobid):
    """Return the current priority of a job.
    
    Parameters:
        jobid: int: the slurm jobid"""
    cmd = ["sprio", "-h", "--jobs", jobid]
    output = sub.Popen(cmd, stdout=sub.PIPE).stdout.read()
    return output.split()[1]

def get_best_account():
    "Return the account which has the highest initial priority"
    prio = {account: 0 for account in get_user_accounts()}
    global test_ids, test_files
    test_ids = []
    test_files = []
    for account in prio.keys():
        filename = os.path.join(os.getcwd(), "test_{}".format(account))
        test_files.append(filename)

        with open(filename, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("#SBATCH --account={}\n".format(account))
        cmd = ["sbatch", filename]
        test_jobid = sub.Popen(cmd, stdout=sub.PIPE).stdout.read().split()[-1]
        prio[account] = get_priority(test_jobid)
        test_ids.append(test_jobid)
    return max(prio, key=prio.get), prio

def kill(jobid):
    "Kill the job"
    sub.call(["scancel", jobid])

def optimize():
    """Update all pending jobs with the best account number.
    Note that this will ONLY changes the FAIRSHARE points of
    the job, and NOT the AGE points.
    
    Therefore you can change back to the previous account if
    you want to, without losing priority."""
    account = get_best_account()[0]
    for job in get_id():
        cmd = ["scontrol", "update", "jobid={}".format(job), "account={}".format(account)]
        sub.call(cmd)
    print("Optimization complete. Best account: {}".format(account))

parser = argparse.ArgumentParser(description="Determine highest priority account, and update pending jobs.")
parser.add_argument("-u", "--update", action="store_true", help="Update all pending jobs to highest priority account")
args = parser.parse_args()

# Run the optimization
if args.update:
    optimize()
else:
    prio = get_best_account()[1]
    print("Fairshare points:")
    for acc, prio in prio.items():
        print("{}: {}".format(acc, prio))

# Clean up
for job in test_ids:
    kill(job)

for f in test_files:
    os.remove(f)
