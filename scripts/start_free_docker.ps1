$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot\..")
docker compose --env-file .env -f editions/free/docker-compose.free.yml up -d --build
docker compose --env-file .env -f editions/free/docker-compose.free.yml ps
