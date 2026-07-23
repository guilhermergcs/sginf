#!/bin/bash
set -euo pipefail

REPO_URL="https://github.com/guilhermergcs/sginf.git"
APP_NAME="sginf"
APP_DIR="/opt/${APP_NAME}"
PORT="${PORT:-5000}"

echo "============================================"
echo "  Setup ${APP_NAME} - Ubuntu (Docker)"
echo "============================================"

if [ "$(id -u)" -ne 0 ]; then
    echo "Execute como root: sudo bash scripts/setup_ubuntu.sh"
    exit 1
fi

if [ -n "${GITHUB_TOKEN:-}" ]; then
    REPO_URL="https://${GITHUB_TOKEN}@github.com/guilhermergcs/sginf.git"
    echo "  Token (via env) configurado."
else
    echo "O repositorio e privado? Se sim, informe o GitHub Personal Access Token."
    echo "Se for publico, pressione Enter para pular."
    echo ""
    read -rp "GITHUB_TOKEN (Enter para pular): " GITHUB_TOKEN

    if [ -n "${GITHUB_TOKEN}" ]; then
        REPO_URL="https://${GITHUB_TOKEN}@github.com/guilhermergcs/sginf.git"
        echo "  Token configurado."
    else
        echo "  Tentando acesso publico..."
    fi
fi

echo "[1/7] Instalando dependencias do sistema..."
apt-get update -qq
apt-get install -y -qq git ca-certificates curl gnupg > /dev/null

echo "[2/7] Instalando Docker..."
if ! command -v docker &>/dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin > /dev/null
    systemctl enable docker --quiet
    systemctl start docker
    echo "  Docker instalado."
else
    echo "  Docker ja instalado: $(docker --version)"
fi

echo "[3/7] Clonando repositorio..."
if [ -d "${APP_DIR}/.git" ]; then
    echo "  Diretorio ja existe. Fazendo git pull..."
    cd "${APP_DIR}"
    git pull --quiet
else
    rm -rf "${APP_DIR}"
    git clone "${REPO_URL}" "${APP_DIR}" --quiet
    cd "${APP_DIR}"
fi
ls -la "${APP_DIR}/docker-compose.yml" || { echo "ERRO: docker-compose.yml nao encontrado em ${APP_DIR}"; exit 1; }
echo "  Repositorio em: ${APP_DIR}"

echo "[4/7] Configurando variaveis de ambiente..."
ENV_FILE="${APP_DIR}/.env"
if [ ! -f "${ENV_FILE}" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    cat > "${ENV_FILE}" <<EOF
SECRET_KEY=${SECRET_KEY}
DATABASE_PATH=/app/data/gestao_ti.db
TELEGRAM_BOT_TOKEN=
COOKIE_SECURE=false
PORT=${PORT}
EOF
    echo "  Arquivo .env criado com SECRET_KEY segura."
else
    if ! grep -q "^SECRET_KEY=." "${ENV_FILE}"; then
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i "1i SECRET_KEY=${SECRET_KEY}" "${ENV_FILE}"
        echo "  SECRET_KEY adicionada ao .env existente."
    else
        echo "  Arquivo .env ja existe com SECRET_KEY."
    fi
fi

echo "[5/7] Criando diretorio de dados..."
mkdir -p "${APP_DIR}/data"

cd "${APP_DIR}"
echo "  Conteudo do diretorio:"
ls -la

echo "[6/7] Build da imagem Docker..."
docker compose build

echo "[7/7] Iniciando container..."
docker compose up -d

sleep 3

echo "  Aguardando container ficar saudavel..."
for i in $(seq 1 10); do
    if docker compose ps --services --filter status=running 2>/dev/null | grep -qx 'web'; then
        echo "  Container pronto!"
        break
    fi
    echo "  Tentativa $i/10..."
    sleep 2
done

if docker compose ps --services --filter status=running 2>/dev/null | grep -qx 'web'; then
    echo ""
    echo "============================================"
    echo "  Aplicacao rodando com sucesso!"
    echo "============================================"
    echo ""
    IP=$(hostname -I | awk '{print $1}')
    echo "  URL:      http://${IP}:${PORT}"
    echo "  Status:   docker compose ps"
    echo "  Logs:     docker compose logs -f"
    echo "  Restart:  docker compose restart"
    echo "  Parar:    docker compose down"
    echo "  Atualizar: cd ${APP_DIR} && git pull && docker compose up -d --build"
    echo ""
    echo "  IMPORTANTE: Edite ${ENV_FILE}"
    echo "  para configurar TELEGRAM_BOT_TOKEN."
    echo ""
else
    echo "ERRO: Container nao iniciou. Verifique:"
    docker compose logs --tail 20
    exit 1
fi
