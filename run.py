import subprocess
import sys
import time
import psutil
import docker
import atexit
import requests
from requests.exceptions import RequestException

processes = []


def is_docker_running():
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception as e:
        print(f"Docker not running or accessible: {e}")
        return False


def run_docker_compose():
    process = subprocess.Popen(["docker-compose", "up", "-d"])
    processes.append(process)
    print("Starting TimescaleDB container...")
    time.sleep(10)


def run_flask():
    process = subprocess.Popen([sys.executable, "server.py"])
    processes.append(process)
    return process


def run_scheduler():
    process = subprocess.Popen([sys.executable, "background/scheduler.py"])
    processes.append(process)
    return process


def wait_for_timescale():
    client = docker.from_env()
    container_name = "timescaledb_container"
    max_attempts = 30

    for _ in range(max_attempts):
        try:
            container = client.containers.get(container_name)
            if container.status == "running":
                inspection = client.api.inspect_container(container.id)
                health_status = inspection["State"]["Running"]

                if health_status:
                    print("TimescaleDB is ready.")
                    return True
        except docker.errors.NotFound:
            print(f"Container {container_name} not found. Waiting...")
        except Exception as e:
            print(f"Error checking TimescaleDB status: {e}")

        time.sleep(2)
    return False


def wait_for_flask(timeout=30, check_interval=0.5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get("http://127.0.0.1:5000")
            # Check if Flask is responding, even with a 404
            if response.status_code in [200, 404]:
                print("Flask is ready.")
                return True
        except RequestException:
            pass
        time.sleep(check_interval)
    print(f"Flask failed to start within {timeout} seconds.")
    return False


def cleanup():
    print("Cleaning up...")
    for process in processes:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    # Stop Docker containers
    subprocess.run(["docker-compose", "down"])

    print("Cleanup complete.")


if __name__ == "__main__":
    atexit.register(cleanup)

    try:
        if not is_docker_running():
            print("Exiting as Docker is not running.")
            sys.exit(1)

        run_docker_compose()

        if not wait_for_timescale():
            print("Exiting due to TimescaleDB startup failure.")
            sys.exit(1)

        flask_process = run_flask()
        if not wait_for_flask():
            print("Error: Flask didn't start properly.")
            sys.exit(1)
        run_scheduler()
        print("All processes started. Press CTRL+C to exit.")

        while True:
            time.sleep(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Exiting...")
