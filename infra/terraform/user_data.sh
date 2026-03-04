#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${repo_url}"
APP_DIR="${app_dir}"
COMPOSE_FILE="${compose_file}"
SSM_PARAMETER_NAME="${ssm_parameter_name}"
AWS_REGION="${aws_region}"

dnf update -y
dnf install -y docker docker-compose-plugin git awscli
systemctl enable --now docker

mkdir -p "$APP_DIR"

if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" pull
fi

if [ -n "$SSM_PARAMETER_NAME" ]; then
  aws ssm get-parameter \
    --name "$SSM_PARAMETER_NAME" \
    --with-decryption \
    --region "$AWS_REGION" \
    --query 'Parameter.Value' \
    --output text > "$APP_DIR/.env"
fi

cat > /etc/systemd/system/openclaw.service <<EOF
[Unit]
Description=OpenClaw bot stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose -f $COMPOSE_FILE up -d --build
ExecStop=/usr/bin/docker compose -f $COMPOSE_FILE down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now openclaw.service
