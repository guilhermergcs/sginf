#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "[*] Pulling latest code..."
git pull

echo "[*] Installing dependencies..."
.venv/bin/pip install -r requirements.txt -q

DOMAIN="${DOMAIN:-sginf.gob.org.br}"
CERT_SRC="/etc/letsencrypt/live/$DOMAIN"
CERT_DST="ssl"

echo "[*] Renewing Let's Encrypt certificate..."
if [ -d "$CERT_SRC" ]; then
    sudo certbot renew --non-interactive --deploy-hook "cp $CERT_SRC/fullchain.pem $CERT_DST/cert.pem && cp $CERT_SRC/privkey.pem $CERT_DST/key.pem"
else
    echo "[!] Certificado Let's Encrypt nao encontrado em $CERT_SRC"
    echo "[!] Execute manualmente: sudo certbot certonly --manual --preferred-challenges=dns -d $DOMAIN"
fi

echo "[*] Configurando RP_ID no systemd..."
SERVICE_FILE="/etc/systemd/system/sginf.service"
if ! grep -q "Environment=RP_ID=" "$SERVICE_FILE" 2>/dev/null; then
    sudo sed -i "/^\[Service\]/a Environment=RP_ID=$DOMAIN" "$SERVICE_FILE"
    sudo systemctl daemon-reload
fi

echo "[*] Restarting service..."
sudo systemctl restart sginf

echo "[+] Deploy concluido."
