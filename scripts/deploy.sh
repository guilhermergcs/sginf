#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "[*] Pulling latest code..."
git pull

echo "[*] Installing dependencies..."
.venv/bin/pip install -r requirements.txt -q

echo "[*] Restarting service..."
sudo systemctl restart sginf

echo "[+] Deploy concluido."
