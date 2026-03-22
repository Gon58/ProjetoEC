import subprocess
import sys


def run(cmd: list[str], step: str):
    print(f"\n=== {step} ===")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"❌ Failed at: {step}")
        sys.exit(1)


def main():
    print("======================================")
    print("🚀 Starting BACKEND DOCKER test pipeline")
    print("======================================")

    run(
        [
            "docker", "compose", "up", "-d",
            "ec-project-postgres",
            "ec-project-mongo",
            "ec-project-chroma",
            "ec-project-ollama",
        ],
        "Starting backend dependencies",
    )

    run(
        [
            "docker", "compose", "build", "ec-project-backend-tests",
        ],
        "Building backend test container",
    )

    run(
        [
            "docker", "compose", "run", "--rm", "ec-project-backend-tests",
        ],
        "Running backend tests in Docker",
    )

    print("\n======================================")
    print("✅ BACKEND TESTS PASSED (DOCKER)")
    print("======================================")


if __name__ == "__main__":
    main()