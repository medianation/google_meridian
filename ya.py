import os
import subprocess
from pathlib import Path

config_path = Path(__file__).parent / "config.yaml"
os.environ["S3_PATH"] = "blablabla"
command = f"datasphere project job execute -p bt1hl9uhbmi9up51ts42 -c {config_path}"
print(command)
try:
    result = subprocess.run(command, shell=True, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
except subprocess.CalledProcessError as e:
    print(e)
    print("Error occurred:")
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)
    raise
