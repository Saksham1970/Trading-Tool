import subprocess
import sys

if __name__ == "__main__":
    flask_process = subprocess.Popen([sys.executable, "server.py"])
    scheduler_process = subprocess.Popen([sys.executable, "scheduler.py"])

    flask_process.wait()
    scheduler_process.wait()
