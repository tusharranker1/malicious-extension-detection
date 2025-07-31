import subprocess

mitm = subprocess.Popen(["mitmproxy", "-s", "mitm_capture.py"])
main = subprocess.Popen(["python", "main_check.py"])

try:
    mitm.wait()
    main.wait()
except KeyboardInterrupt:
    mitm.terminate()
    main.terminate()
