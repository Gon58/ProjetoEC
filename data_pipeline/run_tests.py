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
    print("🚀 Starting FULL DOCKER test pipeline")
    print("======================================")

    # -------------------------------
    # 1. Docker up (tudo)
    # -------------------------------
    run([
        "docker", "compose", "up", "-d",
        "ec-project-postgres",
        "ec-project-mongo",
        "ec-project-chroma"
    ], "Starting DB services")

    # -------------------------------
    # 2. Build test container
    # -------------------------------
    run([
        "docker", "compose", "build", "ec-project-tests"
    ], "Building test container")

    # -------------------------------
    # 3. Run tests (tudo dentro docker)
    # -------------------------------
    run([
        "docker", "compose", "run", "--rm", "ec-project-tests"
    ], "Running ALL tests in Docker")

    print("\n======================================")
    print("✅ ALL TESTS PASSED (DOCKER)")
    print("======================================")


if __name__ == "__main__":
    main()