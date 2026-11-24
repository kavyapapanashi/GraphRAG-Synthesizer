"""
Unified Single-Server Launcher for GraphRAG
Starts the FastAPI backend and serves the full React frontend + API on http://localhost:8000
"""

import os
import sys
import subprocess
import webbrowser
import time
import uvicorn

# Ensure repository root is on sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Antivirus proxy fix for Windows ssl module
if "SSLKEYLOGFILE" in os.environ and ("aswMonFltProxy" in os.environ["SSLKEYLOGFILE"] or not os.path.exists(os.environ["SSLKEYLOGFILE"])):
    os.environ.pop("SSLKEYLOGFILE", None)

def free_port(port: int = 8000):
    """Cleanly terminates any stale background process holding the target port."""
    if sys.platform == "win32":
        try:
            cmd = f'netstat -ano | findstr LISTENING | findstr :{port}'
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, _ = proc.communicate()
            if out:
                for line in out.decode().strip().split("\n"):
                    parts = line.split()
                    if len(parts) >= 5 and "LISTENING" in parts:
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) != os.getpid() and int(pid) > 0:
                            print(f"[Launcher] Freeing port {port} (terminating stale process PID {pid})...")
                            subprocess.call(f'taskkill /F /PID {pid}', shell=True)
                            time.sleep(0.5)
        except Exception as e:
            print(f"[Launcher] Port cleanup check: {e}")

if __name__ == "__main__":
    port = 8000
    host = "127.0.0.1"
    url = f"http://localhost:{port}"

    free_port(port)
    
    print("\n" + "=" * 66)
    print("  GRAPHRAG MULTI-PAPER RESEARCH & STUDY SYNTHESIZER")
    print(f"  Access Full Web Workspace: {url}")
    print(f"  Backend Swagger API Docs:  {url}/docs")
    print("=" * 66 + "\n")
    
    # Auto-open browser
    try:
        webbrowser.open(url)
    except Exception:
        pass
        
    uvicorn.run("api.main:app", host=host, port=port, reload=False)
