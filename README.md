# Smallstep CA Nginx Proxy Manager Plugin

## Introduction

This plugin is a small automation tool that monitors Nginx Proxy Manager for additions to proxy hosts. All proxy hosts
that are added without any form of SSL certificate will have a certificate generated using Smallstep's step-cli.

## Setup
To run the manager, you simply need to run the container using either the CLI arguments or corresponding ENV variables.

### Docker Compose Example
```YAML
version: '3.8'

services:
  step-npm-plugin:
    container_name: step-npm-plugin
    image: majorleaguedale/step-npm-plugin:latest
    restart: always
    environment:
      - LOG_LEVEL=INFO
      - STEP_CA_DOMAIN=ca.example.com               # Step CA Domain Name
      - STEP_CA_FINGERPRINT=cr3987adeef348c8d89a890 # Step CA Fingerprint
      - STEP_CA_PROVISIONER_PASS=<MyPassword>       # CA Provisioner password (See DOCKER_STEPCA_INIT_PASSWORD)
      - NPM_USER=user@example.com                   # User will need to be created in NPM manually
      - NPM_PASS=<MyPassword>                       # Password for user manually created in NPM
```

### Settings & Configuration

"*" required

| Env Variable                  | CLI Switch  | Description                                                                                  | Values/Examples                       | Default |
|-------------------------------|-------------|----------------------------------------------------------------------------------------------|---------------------------------------|---------|
| `LOG_LEVEL`                   | --log-level | Log level for the plugin to use.                                                             | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO    |
| `SCHEDULE`                    | --schedule  | Plugin run interval. Can be specified as seconds, minutes, hours up to the maximum of 1 day. | 10s, 20m, 4h                          | 10s     |
| `STEP_CA_SCHEME`              | -ss         | Scheme used by Step CA (http/https)                                                          | http or https                         | https   |
| `STEP_CA_DOMAIN`*             | -sd         | Domain Name to reach step CA                                                                 | ca.example.com                        | -       |
| `STEP_CA_PORT`                | -sp         | Port number used by Step CA                                                                  | 9000                                  | 9000    |
| `STEP_CA_FINGERPRINT`*        | -sf         | Fingerprint to identify Step CA                                                              | -                                     | -       |
| `STEP_CA_PROVISIONER_PASS`*   | -spw        | Provisioner Password to decrypt the JWT for Step-CLI                                         | -                                     | -       |
| `NPM_SCHEME`                  | -ns         | Nginx Proxy Manager Scheme to access the *management* interface                              | http or https                         | http    |
| `NPM_HOST`*                   | -nh         | Nginx Proxy Manager IP or Hostname                                                           | npm.example.com                       | -       |
| `NPM_PORT`                    | -np         | Nginx Proxy Manager Port Number                                                              | 81                                    | 81      |
| `NPM_USER`*                   | -nu         | Nginx Proxy Manager Username                                                                 | user@example.com                      | -       |
| `NPM_PASS`*                   | -npw        | Nginx Proxy Manager Password                                                                 | -                                     | -       |
  