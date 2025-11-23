from typing import List, Dict, Any

def classify_gpus(gpu_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Classifies GPUs into tiers based on hardware capabilities.
    
    Tiers:
    - Tier B (Inference): PCIe Width >= x8.
    - Tier C (Rendering/ZKP): PCIe Width < x8.
    """
    classified_data = []
    
    for gpu in gpu_data:
        # Create a copy to avoid mutating the original dictionary if needed elsewhere
        gpu_info = gpu.copy()
        
        pcie_width = gpu_info.get("pcie_width_current", -1)
        
        if pcie_width >= 8:
            gpu_info["tier"] = "Tier B"
            gpu_info["classification_reason"] = f"High Bandwidth (x{pcie_width})"
        else:
            gpu_info["tier"] = "Tier C"
            gpu_info["classification_reason"] = f"Low Bandwidth (x{pcie_width}) - Mining Rig Detected"
            
        classified_data.append(gpu_info)
        
    return classified_data

if __name__ == "__main__":
    import json
    
    # Test Case 1: Mock Data (RTX 3090 @ x1)
    mock_data = [
        {
            "index": 0,
            "name": "NVIDIA GeForce RTX 3090",
            "uuid": "GPU-MOCK-UUID-1234-5678",
            "pci_bus_id": "0000:01:00.0",
            "memory_total": 24576,
            "pcie_gen_current": 1,
            "pcie_width_current": 1,
            "driver_version": "535.104"
        }
    ]
    
    print("--- Test Case 1: Mock Data (Mining Rig) ---")
    results_mock = classify_gpus(mock_data)
    print(json.dumps(results_mock, indent=4))
    
    # Test Case 2: Ideal Data (RTX 4090 @ x16)
    ideal_data = [
        {
            "index": 0,
            "name": "NVIDIA GeForce RTX 4090",
            "uuid": "GPU-IDEAL-UUID-9999-8888",
            "pci_bus_id": "0000:02:00.0",
            "memory_total": 24576,
            "pcie_gen_current": 4,
            "pcie_width_current": 16,
            "driver_version": "535.104"
        }
    ]
    
    print("\n--- Test Case 2: Ideal Data (Inference Node) ---")
    results_ideal = classify_gpus(ideal_data)
    print(json.dumps(results_ideal, indent=4))
