import psutil
import time
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - CONTROLLER - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MinerController:
    def __init__(self):
        self.miner_pid = None
        # List of common miner process names + our mock
        self.miner_names = ["mock_miner", "t-rex", "nbminer", "bminer", "gminer", "lolminer"]

    def find_miner_pid(self):
        """Scans running processes for known miner names."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check name and cmdline (for python scripts)
                name = proc.info['name'].lower()
                cmdline = proc.info['cmdline'] or []
                cmdline_str = " ".join(cmdline).lower()

                for miner in self.miner_names:
                    # Check if miner name is in process name or cmdline
                    if miner in name or (("python" in name) and (miner in cmdline_str)):
                         # Avoid killing self or unrelated python scripts
                         if "process_controller" in cmdline_str or "main.py" in cmdline_str:
                             continue
                         
                         self.miner_pid = proc.info['pid']
                         logger.info(f"Found Miner Process: {miner} (PID: {self.miner_pid})")
                         return self.miner_pid
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        logger.warning("No active miner process found.")
        return None

    # RENAMED from pause_miner to pause to match main.py
    def pause(self):
        """Pauses the miner process (SIGSTOP)."""
        if not self.miner_pid:
            self.find_miner_pid()
        
        if self.miner_pid:
            try:
                proc = psutil.Process(self.miner_pid)
                proc.suspend()
                logger.info(f"Miner PAUSED (PID: {self.miner_pid})")
            except psutil.NoSuchProcess:
                logger.error(f"Miner process {self.miner_pid} no longer exists.")
                self.miner_pid = None
            except Exception as e:
                logger.error(f"Failed to pause miner: {e}")

    # RENAMED from resume_miner to resume to match main.py
    def resume(self):
        """Resumes the miner process (SIGCONT)."""
        if self.miner_pid:
            try:
                proc = psutil.Process(self.miner_pid)
                proc.resume()
                logger.info(f"Miner RESUMED (PID: {self.miner_pid})")
            except psutil.NoSuchProcess:
                logger.error(f"Miner process {self.miner_pid} no longer exists.")
                self.miner_pid = None
            except Exception as e:
                logger.error(f"Failed to resume miner: {e}")

if __name__ == "__main__":
    controller = MinerController()
    pid = controller.find_miner_pid()
    if pid:
        controller.pause()
        print("--- AI Job Running (5s) ---")
        time.sleep(5)
        controller.resume()
    else:
        print("Test Failed: Could not find mock_miner.")