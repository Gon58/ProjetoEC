import shlex
import subprocess
import sys

CRON = "0 3 * * *"  # daily at 03:00
FLOW_REF = "ingestion_flow.py:ingestion_flow"
WORK_POOL = "local-pool"

DEPLOY_COMMAND = [
    "prefect",
    "deploy",
    "/flows/ingestion_flow.py:ingestion_flow",
    "-n",
    "ingestion",
    "--pool",
    WORK_POOL,
    "--cron",
    CRON,
    "--no-prompt",
]


def run_cmd(cmd):
    print("RUN:", " ".join(shlex.quote(c) for c in cmd))
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("Command failed:", e)
        return False


def main():
    print("Deploy helper: registering ingestion_flow deployment")
    if run_cmd(DEPLOY_COMMAND):
        print("Deployment command succeeded")
        return 0
    print("If the work pool does not exist yet, create it once with:")
    print(" ", "prefect work-pool create local-pool --type process")
    print("If needed, run `python /flows/ingestion_flow.py` to test the flow locally.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
