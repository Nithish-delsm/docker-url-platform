#!/bin/bash
set -e
cd /home/ec2-user/docker-url-platform
export API_IMAGE="$1"
REGISTRY="${API_IMAGE%%/*}"
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin "$REGISTRY"
docker compose pull api
docker compose up -d
docker image prune -f
