#!/usr/bin/env bash
# Initial host configuration for the Career Compass AWS EC2 instance.
# Run through AWS Systems Manager only; it intentionally contains no secrets.
set -euo pipefail

APP_NAME="career-compass"
APP_USER="careercompass"
APP_ROOT="/opt/${APP_NAME}"
PARAMETER_NAME="${PARAMETER_NAME:?PARAMETER_NAME must be set}"
AWS_REGION="${AWS_REGION:?AWS_REGION must be set}"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  nginx python3.12 python3.12-venv python3-pip jq ca-certificates curl git unzip
curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp
/tmp/aws/install --update
rm -rf /tmp/aws /tmp/awscliv2.zip
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y --no-install-recommends nodejs

id -u "${APP_USER}" >/dev/null 2>&1 || useradd --system --create-home --home-dir "${APP_ROOT}" --shell /usr/sbin/nologin "${APP_USER}"
install -d -o "${APP_USER}" -g "${APP_USER}" -m 0755 "${APP_ROOT}/releases" "${APP_ROOT}/shared"

cat >/usr/local/sbin/career-compass-sync-secrets <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
PARAMETER_NAME="__PARAMETER_NAME__"
AWS_REGION="__AWS_REGION__"
OUTPUT="/opt/career-compass/shared/backend.env"
TEMP_FILE="$(mktemp)"
trap 'rm -f "$TEMP_FILE"' EXIT

aws ssm get-parameter \
  --name "$PARAMETER_NAME" \
  --with-decryption \
  --region "$AWS_REGION" \
  --query Parameter.Value \
  --output text >"$TEMP_FILE"

jq -r 'to_entries[] | select(.value != null) | "\(.key)=\(.value|@json)"' "$TEMP_FILE" >"$OUTPUT"
chown careercompass:careercompass "$OUTPUT"
chmod 0600 "$OUTPUT"
EOF
sed -i "s|__PARAMETER_NAME__|${PARAMETER_NAME}|g; s|__AWS_REGION__|${AWS_REGION}|g" /usr/local/sbin/career-compass-sync-secrets
chmod 0755 /usr/local/sbin/career-compass-sync-secrets

cat >/usr/local/sbin/career-compass-deploy <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/opt/career-compass"
SOURCE_DIR="${APP_ROOT}/source"
REPOSITORY="https://github.com/RaoHasnain-016/career-compass-ai.git"

if [ ! -d "${SOURCE_DIR}/.git" ]; then
  rm -rf "$SOURCE_DIR"
  git clone --depth 1 --branch main "$REPOSITORY" "$SOURCE_DIR"
else
  git -C "$SOURCE_DIR" fetch --depth 1 origin main
  git -C "$SOURCE_DIR" reset --hard origin/main
fi

cd "$SOURCE_DIR"
npm ci --prefix frontend
npm run build --prefix frontend
python3.12 -m venv "$SOURCE_DIR/venv"
"$SOURCE_DIR/venv/bin/pip" install --disable-pip-version-check --no-cache-dir -r "$SOURCE_DIR/backend/requirements.txt"
chown -R careercompass:careercompass "$SOURCE_DIR"
ln -sfn "$SOURCE_DIR" "${APP_ROOT}/current"
systemctl daemon-reload
systemctl restart career-compass
EOF
chmod 0750 /usr/local/sbin/career-compass-deploy

cat >/etc/systemd/system/career-compass.service <<'EOF'
[Unit]
Description=Career Compass AI FastAPI application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=careercompass
Group=careercompass
WorkingDirectory=/opt/career-compass/current/backend
Environment=DATABASE_AUTO_CREATE=false
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/opt/career-compass/shared/backend.env
ExecStartPre=/usr/local/sbin/career-compass-sync-secrets
ExecStart=/opt/career-compass/current/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=/opt/career-compass

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/career-compass-deploy.service <<'EOF'
[Unit]
Description=Update Career Compass from GitHub
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/career-compass-deploy
EOF

cat >/etc/systemd/system/career-compass-deploy.timer <<'EOF'
[Unit]
Description=Check Career Compass GitHub repository for updates

[Timer]
OnBootSec=2min
OnUnitActiveSec=2min
Persistent=true

[Install]
WantedBy=timers.target
EOF

cat >/etc/nginx/sites-available/career-compass <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 2m;
    proxy_connect_timeout 10s;
    proxy_read_timeout 60s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/career-compass /etc/nginx/sites-enabled/career-compass
nginx -t
systemctl daemon-reload
systemctl enable nginx career-compass career-compass-deploy.timer
systemctl restart nginx
/usr/local/sbin/career-compass-deploy
systemctl start career-compass-deploy.timer
