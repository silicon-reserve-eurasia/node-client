import docker
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - CONTAINER MGR - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_container(image: str, command: str, use_gpu: bool = False, timeout: int = 300) -> str:
    """
    Runs a Docker container with optional GPU support and a strict timeout.
    """
    client = None
    container = None
    
    try:
        client = docker.from_env()
    except docker.errors.DockerException:
        logger.error("Docker is not running or not installed.")
        return "DOCKER_ERROR"

    try:
        # 1. Pull Image
        try:
            client.images.get(image)
        except docker.errors.ImageNotFound:
            logger.info(f"Pulling image: {image}...")
            client.images.pull(image)

        # 2. Configure GPU Request
        device_requests = []
        if use_gpu:
            try:
                # Request all GPUs
                device_requests.append(docker.types.DeviceRequest(count=-1, capabilities=[['gpu']]))
                logger.info("GPU Passthrough Enabled.")
            except Exception as e:
                logger.warning(f"Failed to configure GPU request: {e}. Falling back to CPU.")

        # 3. Run Container (Detached)
        logger.info(f"Starting container: {image} (Timeout: {timeout}s)")
        container = client.containers.run(
            image,
            command,
            detach=True,
            device_requests=device_requests
        )

        # 4. Watchdog (Timeout Logic)
        start_time = time.time()
        while True:
            container.reload() # Refresh status
            if container.status == 'exited':
                break
            
            if time.time() - start_time > timeout:
                logger.error(f"Container timed out after {timeout}s. Killing...")
                container.kill()
                raise TimeoutError(f"Container execution exceeded {timeout}s limit.")
            
            time.sleep(1) # Poll every second

        # 5. Capture Logs
        logs = container.logs().decode('utf-8').strip()
        return logs

    except TimeoutError as te:
        return f"TIMEOUT_ERROR: {str(te)}"
    except Exception as e:
        logger.error(f"Container Execution Failed: {e}")
        return f"EXECUTION_ERROR: {str(e)}"
        
    finally:
        # 6. Cleanup
        if container:
            try:
                container.remove(force=True)
                logger.info("Container removed.")
            except Exception as e:
                logger.warning(f"Failed to remove container: {e}")

if __name__ == "__main__":
    # Verification Test
    print("--- Starting Verification ---")
    
    # Test 1: CPU Test (Alpine)
    result = run_container("alpine", "echo 'Apex CPU Test'", use_gpu=False, timeout=10)
    print(f"Result: {result}")

    # Test 2: GPU Test (Commented out for Mac/Dev)
    # print(run_container("nvidia/cuda:11.0-base", "nvidia-smi", use_gpu=True))
