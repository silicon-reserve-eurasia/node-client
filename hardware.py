import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import pynvml
except ImportError:
    pynvml = None

class MockNVML:
    """
    Mock NVML class to simulate GPU environment on non-GPU machines.
    Simulates an RTX 3090 on PCIe x1 (Mining Rig Scenario).
    """
    
    # Mock Constants
    NVML_PCIE_UTIL_TX_BYTES = 0
    NVML_PCIE_UTIL_RX_BYTES = 1
    
    @staticmethod
    def nvmlInit():
        logger.warning("MockNVML: Initialized (Mock Mode)")
        return

    @staticmethod
    def nvmlDeviceGetCount():
        return 1

    @staticmethod
    def nvmlDeviceGetHandleByIndex(index):
        if index == 0:
            return "MockHandle_0"
        raise Exception("Invalid device index")

    @staticmethod
    def nvmlDeviceGetName(handle):
        return "NVIDIA GeForce RTX 3090"

    @staticmethod
    def nvmlDeviceGetUUID(handle):
        return "GPU-MOCK-UUID-1234-5678"

    @staticmethod
    def nvmlDeviceGetPciInfo(handle):
        class MockPciInfo:
            busId = b"0000:01:00.0"
        return MockPciInfo()

    @staticmethod
    def nvmlDeviceGetMemoryInfo(handle):
        class MockMemory:
            total = 24576 * 1024 * 1024  # 24GB in bytes
            free = 20000 * 1024 * 1024
            used = 4576 * 1024 * 1024
        return MockMemory()

    @staticmethod
    def nvmlDeviceGetPcieLinkWidth(handle):
        return 1  # Simulating x1 width (Mining Rig)

    @staticmethod
    def nvmlDeviceGetMaxPcieLinkWidth(handle):
        return 16

    @staticmethod
    def nvmlDeviceGetCurrPcieLinkGeneration(handle):
        return 1 # Simulating Gen 1

    @staticmethod
    def nvmlDeviceGetMaxPcieLinkGeneration(handle):
        return 4

    @staticmethod
    def nvmlSystemGetDriverVersion():
        return "535.104"

    @staticmethod
    def nvmlShutdown():
        logger.info("MockNVML: Shutdown")

    @staticmethod
    def nvmlDeviceGetTemperature(handle, sensor_type):
        return 65 # Mock temperature

def audit_gpu() -> List[Dict[str, Any]]:
    """
    Audits the host machine's GPU capabilities.
    Returns a list of dictionaries containing GPU metrics.
    """
    nvml = pynvml
    using_mock = False

    if nvml is None:
        logger.warning("pynvml not installed, falling back to MockNVML")
        nvml = MockNVML
        using_mock = True
    else:
        try:
            nvml.nvmlInit()
        except Exception as e: # Catching generic exception as pynvml might raise different errors
            logger.warning(f"Failed to initialize NVML: {e}. Falling back to MockNVML")
            nvml = MockNVML
            using_mock = True
            nvml.nvmlInit()

    gpu_data = []
    try:
        device_count = nvml.nvmlDeviceGetCount()
        for i in range(device_count):
            handle = nvml.nvmlDeviceGetHandleByIndex(i)
            
            name = nvml.nvmlDeviceGetName(handle)
            # Handle bytes vs string return types which can vary by version
            if isinstance(name, bytes):
                name = name.decode('utf-8')
                
            uuid = nvml.nvmlDeviceGetUUID(handle)
            if isinstance(uuid, bytes):
                uuid = uuid.decode('utf-8')
                
            pci_info = nvml.nvmlDeviceGetPciInfo(handle)
            pci_bus_id = pci_info.busId
            if isinstance(pci_bus_id, bytes):
                pci_bus_id = pci_bus_id.decode('utf-8')

            memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)
            memory_total_mb = int(memory_info.total / 1024 / 1024)

            # Critical PCIe Checks
            try:
                pcie_width_current = nvml.nvmlDeviceGetPcieLinkWidth(handle)
                pcie_gen_current = nvml.nvmlDeviceGetCurrPcieLinkGeneration(handle)
            except Exception:
                 # Fallback for older drivers/cards or mock limitations if not fully implemented
                pcie_width_current = -1
                pcie_gen_current = -1

            driver_version = nvml.nvmlSystemGetDriverVersion()
            if isinstance(driver_version, bytes):
                driver_version = driver_version.decode('utf-8')

            try:
                # 0 = NVML_TEMPERATURE_GPU
                temperature = nvml.nvmlDeviceGetTemperature(handle, 0)
            except:
                temperature = 0

            gpu_info = {
                "index": i,
                "name": name,
                "uuid": uuid,
                "pci_bus_id": pci_bus_id,
                "memory_total": memory_total_mb,
                "pcie_gen_current": pcie_gen_current,
                "pcie_width_current": pcie_width_current,
                "pcie_width_current": pcie_width_current,
                "driver_version": driver_version,
                "temperature": temperature
            }
            gpu_data.append(gpu_info)

    except Exception as e:
        logger.error(f"Error during GPU audit: {e}")
    finally:
        try:
            nvml.nvmlShutdown()
        except:
            pass

    return gpu_data

# Alias for compatibility with Apex Node
scan_system = audit_gpu

if __name__ == "__main__":
    import json
    # For local testing/verification
    results = scan_system()
    print(json.dumps(results, indent=4))
