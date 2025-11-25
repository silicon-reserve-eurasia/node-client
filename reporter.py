from fpdf import FPDF
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ApexReport(FPDF):
    def header(self):
        # BRANDING UPDATE: Silicon Reserve Eurasia
        self.set_font('Courier', 'B', 14)
        self.cell(0, 10, 'SILICON RESERVE EURASIA | INFRASTRUCTURE AUDIT', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Courier', 'I', 8)
        self.cell(0, 10, 'This document acts as a preliminary technical assessment for the Reserve Hashrate Swap Agreement.', align='C')

def generate_report(nodes: List[Dict[str, Any]], filename: str = "Silicon_Reserve_Audit.pdf"):
    """
    Generates a PDF report for the audited GPUs.
    """
    pdf = ApexReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Timestamp
    pdf.set_font('Courier', '', 10)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    pdf.cell(0, 10, f"Timestamp: {timestamp}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Table Header
    pdf.set_font('Courier', 'B', 10)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(60, 10, "Model Name", border=1, fill=True)
    pdf.cell(50, 10, "UUID (Truncated)", border=1, fill=True)
    pdf.cell(30, 10, "PCIe Status", border=1, fill=True)
    pdf.cell(50, 10, "Certified Tier", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    # Table Rows
    pdf.set_font('Courier', '', 10)
    
    for node in nodes:
        name = node.get("name", "Unknown")
        uuid = node.get("uuid", "Unknown")[-8:] # Truncate UUID
        pcie_width = node.get("pcie_width_current", -1)
        tier = node.get("tier", "Unknown")
        
        pdf.cell(60, 10, name, border=1)
        pdf.cell(50, 10, uuid, border=1)
        
        # PCIe Status Color Coding
        if pcie_width >= 8:
            pdf.set_text_color(0, 128, 0) # Green
            status_text = f"x{pcie_width} (OK)"
        else:
            pdf.set_text_color(255, 0, 0) # Red
            status_text = f"x{pcie_width} (FAIL)"
            
        pdf.cell(30, 10, status_text, border=1)
        pdf.set_text_color(0, 0, 0) # Reset to black
        
        # Tier Font Size
        pdf.set_font('Courier', 'B', 12)
        pdf.cell(50, 10, tier, border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Courier', '', 10) # Reset font

    pdf.ln(10)

    # Financial Hook Logic
    is_tier_c = any(n.get("tier") == "Tier C" for n in nodes)
    
    pdf.set_font('Courier', 'B', 12)
    if not is_tier_c:
        # Tier B Hook
        pdf.set_fill_color(220, 255, 220) # Light Green
        pdf.multi_cell(0, 15, "SILICON RESERVE SUBSIDY: QUALIFIED. EST. CREDIT: $2.10/hr", border=1, align='C', fill=True)
    else:
        # Tier C Hook
        pdf.set_fill_color(255, 220, 220) # Light Red
        pdf.multi_cell(0, 15, "SILICON RESERVE SUBSIDY: RESTRICTED. EST. CREDIT: $0.35/hr\nACTION REQUIRED: Upgrade PCIe risers to x8 or higher.", border=1, align='C', fill=True)

    try:
        pdf.output(filename)
        logger.info(f"Report generated successfully: {filename}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")

if __name__ == "__main__":
    # Mock Data for Verification
    mock_nodes = [
        {
            "index": 0,
            "name": "NVIDIA GeForce RTX 3090",
            "uuid": "GPU-MOCK-UUID-1234-5678",
            "pci_bus_id": "0000:01:00.0",
            "memory_total": 24576,
            "pcie_gen_current": 1,
            "pcie_width_current": 1,
            "driver_version": "535.104",
            "tier": "Tier C",
            "classification_reason": "Low Bandwidth (x1) - Mining Rig Detected"
        }
    ]
    
    generate_report(mock_nodes, "Apex_Audit_Cert_Mock.pdf")
    
    ideal_nodes = [
        {
            "index": 0,
            "name": "NVIDIA GeForce RTX 4090",
            "uuid": "GPU-IDEAL-UUID-9999-8888",
            "pci_bus_id": "0000:02:00.0",
            "memory_total": 24576,
            "pcie_gen_current": 4,
            "pcie_width_current": 16,
            "driver_version": "535.104",
            "tier": "Tier B",
            "classification_reason": "High Bandwidth (x16)"
        }
    ]
    generate_report(ideal_nodes, "Apex_Audit_Cert_Ideal.pdf")
