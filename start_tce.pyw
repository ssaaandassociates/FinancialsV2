"""
TCE Engine — Silent Desktop Launcher
Runs the server without showing a console window.
Double-click start_tce.pyw to launch.
"""
import subprocess
import webbrowser
import time
import sys
import os

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Start uvicorn as a subprocess
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=0x08000000 if os.name == 'nt' else 0,  # CREATE_NO_WINDOW on Windows
)

# Wait and open browser
time.sleep(3)
webbrowser.open("http://127.0.0.1:8000/")

# Keep running until process ends
try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
