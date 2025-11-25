#!/bin/bash
# Silicon Reserve Eurasia - Node Initialization (GPU Enabled)
# Usage: curl -sL https://raw.githubusercontent.com/silicon-reserve-eurasia/node-client/main/install.sh | bash

# --- CONFIGURATION ---
ORG_NAME="silicon-reserve-eurasia"
REPO_NAME="node-client"
BRANCH="main"
# ---------------------

echo -e "\033[0;36m[SILICON RESERVE] Initializing Sovereign Node...\033[0m"

# 1. Setup Environment
mkdir -p ~/apex_node
cd ~/apex_node

# 2. Install System Dependencies & Docker
echo "[*] Checking System..."
if [ -x "$(command -v apt-get)" ]; then
    sudo apt-get update -qq
    sudo apt-get install -y python3-pip docker.io curl > /dev/null 2>&1
fi

# --- NEW: NVIDIA Container Toolkit Installation (The GPU Enabler) ---
echo "[*] Configuring GPU Passthrough..."
if command -v nvidia-smi &> /dev/null; then
    # Only install if NVIDIA GPU is present
    if ! command -v nvidia-ctk &> /dev/null; then
        echo "    - Adding NVIDIA Repositories..."
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
        && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null
        
        sudo apt-get update -qq
        sudo apt-get install -y nvidia-container-toolkit > /dev/null 2>&1
        
        # Configure Docker to use NVIDIA
        sudo nvidia-ctk runtime configure --runtime=docker > /dev/null 2>&1
        sudo systemctl restart docker
        echo "    - GPU Bridge Installed."
    else
        echo "    - GPU Bridge already present."
    fi
else
    echo "    [!] Warning: No NVIDIA GPU detected. Node will run in CPU Mode."
fi
# --------------------------------------------------------------------

# 3. Download Protocols (Direct from GitHub Public Repo)
echo "[*] Fetching Reserve Protocols..."
BASE_URL="https://raw.githubusercontent.com/$ORG_NAME/$REPO_NAME/$BRANCH"

# Core Files
curl -sL "$BASE_URL/main.py" -o main.py
curl -sL "$BASE_URL/container_manager.py" -o container_manager.py
curl -sL "$BASE_URL/process_controller.py" -o process_controller.py
curl -sL "$BASE_URL/requirements.txt" -o requirements.txt

# Audit Modules
curl -sL "$BASE_URL/hardware.py" -o hardware.py
curl -sL "$BASE_URL/classifier.py" -o classifier.py
curl -sL "$BASE_URL/reporter.py" -o reporter.py

# 4. Install Python Libs
echo "[*] Installing Dependencies..."
pip3 install -r requirements.txt > /dev/null 2>&1

# 5. Persistence (Systemd)
echo "[*] Establishing Service..."
sudo bash -c 'cat > /etc/systemd/system/apex.service <<EOF
[Unit]
Description=Silicon Reserve Node
After=network.target docker.service

[Service]
User=root
WorkingDirectory=/root/apex_node
ExecStart=/usr/bin/python3 /root/apex_node/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF'

# 6. Ignite
sudo systemctl daemon-reload
sudo systemctl enable apex
sudo systemctl restart apex

echo -e "\033[0;32m[SUCCESS] Node Online. Connected to Reserve C2.\033[0m"
