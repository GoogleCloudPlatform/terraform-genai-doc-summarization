
mkdir -p ~/lab/scripts ~/lab/logs

cat > ~/lab/scripts/kitsune-diagnostico.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -u
umask 077

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$(python -c \
'import secrets; print(secrets.token_hex(4))')"

LOG="$HOME/lab/logs/kitsune-${RUN_ID}.log"

exec > >(tee "$LOG") 2>&1

echo "===== KITSUNE: DIAGNOSTICO ====="
echo "RUN_ID=$RUN_ID"
echo "UTC=$(date -u +%FT%TZ)"
echo

echo "===== IDENTIDAD Y PERMISOS ====="
id
echo "UID=$(id -u)"
echo

echo "===== KERNEL Y ARQUITECTURA ====="
uname -a
echo

echo "===== AIREPLAY-NG ====="
command -v aireplay-ng || echo "No instalado o no visible"
echo

echo "===== IW ====="
command -v iw || echo "No instalado o no visible"
echo

echo "===== INTERFACES WI-FI ====="
if command -v iw >/dev/null 2>&1; then
    iw dev 2>&1
else
    echo "No se puede consultar iw"
fi
echo

echo "===== CAPACIDADES DEL DRIVER ====="
if command -v iw >/dev/null 2>&1; then
    iw list 2>&1
else
    echo "No se puede consultar el controlador"
fi

echo
echo "===== GITHUB CLI ====="
if command -v gh >/dev/null 2>&1; then
    gh --version | head -n 1
    gh auth status 2>&1 || true
else
    echo "gh no instalado"
fi

echo
echo "===== FIN ====="
echo "Registro: $LOG"
EOF

chmod 700 ~/lab/scripts/kitsune-diagnostico.sh
bash ~/lab/scripts/kitsune-diagnostico.sh
