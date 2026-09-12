#!/usr/bin/env python3
"""
Project JANUS: Automated Synchronization Tool for janus-simulation Repository

This script synchronizes changes from the primary hardware repository's `janus_mini16_sim`
directory into the dedicated `janus-simulation` git repository (tracked as remote `sim`).

Usage:
    python scripts/sync_simulation_repo.py [--push] [--message "Commit message"]
"""

import argparse
import os
import subprocess
import sys

SIM_REMOTE = "sim"
SIM_BRANCH = "sim-main"
SIM_REMOTE_BRANCH = "main"

def run_git(args, check=True):
    res = subprocess.run(["git"] + args, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"Error executing 'git {' '.join(args)}':\n{res.stderr}", file=sys.stderr)
        sys.exit(res.returncode)
    return res

def main():
    parser = argparse.ArgumentParser(description="Sync janus_mini16_sim to janus-simulation repository.")
    parser.add_argument("--push", action="store_true", default=True, help="Push changes to remote sim/main (default: True)")
    parser.add_argument("--no-push", dest="push", action="store_false", help="Do not push changes to remote")
    parser.add_argument("-m", "--message", default="chore(sync): update simulation suite from main repository", help="Commit message")
    args = parser.parse_args()

    # Verify git status is clean on current branch
    st = run_git(["status", "--porcelain"])
    if st.stdout.strip():
        print("ERROR: Working tree is not clean. Please commit or stash changes before syncing.", file=sys.stderr)
        sys.exit(1)

    # Get current branch name
    cur_branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    print(f"[*] Current branch: {cur_branch}")

    print("[*] Fetching from sim remote...")
    run_git(["fetch", SIM_REMOTE])

    print(f"[*] Switching to {SIM_BRANCH}...")
    run_git(["checkout", SIM_BRANCH])

    print("[*] Checking out latest janus_mini16_sim from main...")
    run_git(["checkout", "main", "--", "janus_mini16_sim"])

    # Stage changes
    run_git(["add", "-A"])
    diff_check = run_git(["diff", "--cached", "--quiet"], check=False)

    if diff_check.returncode == 0:
        print("[+] Janus-simulation is already completely up to date. Nothing to commit.")
    else:
        print(f"[*] Committing changes: {args.message}")
        run_git(["commit", "-m", args.message])
        print("[+] Successfully committed updates.")

        if args.push:
            print(f"[*] Pushing to {SIM_REMOTE}/{SIM_REMOTE_BRANCH}...")
            run_git(["push", SIM_REMOTE, f"{SIM_BRANCH}:{SIM_REMOTE_BRANCH}"])
            print("[+] Successfully pushed updates to janus-simulation repository!")

    print(f"[*] Switching back to {cur_branch}...")
    run_git(["checkout", cur_branch])
    print("[*] Synchronization complete!")

if __name__ == "__main__":
    main()
