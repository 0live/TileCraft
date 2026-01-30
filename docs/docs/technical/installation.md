---
sidebar_position: 1.5
---

# Deployment Guide

This guide explains how to deploy Canopy in production. It is designed for system administrators or operations teams.

## 1. Requirements

Detailed installation instructions are out of scope for this guide, but you must have the following installed on your server:

- **Docker Desktop** (Mac/Windows)
- **Docker Engine** + **Docker Compose Plugin** (Linux)
- **Make** (standard utility on Linux/Unix)

### Operating System Support

- **Linux**: Supported natively (Recommended for production).
- **Windows**: Use **WSL 2** (Windows Subsystem for Linux).
  > [!IMPORTANT]
  > Ensure "Use the WSL 2 based engine" is enabled in Docker Desktop settings.
  > All commands must be run from within the WSL Linux terminal, not PowerShell/CMD.

## 2. Configuration

Canopy is configured entirely through environment variables. You must create a configuration file named `.env.local` to override the defaults.

### Setup Step

1. Creating the configuration file:

   ```bash
   touch .env.local
   ```

2. Open this file and add the following configuration blocks, replacing the values with your own.

### Configuration Values

Copy and paste these blocks into your `.env.local` file and adjust the values.

#### Database Settings

Crucial for data access.

- `POSTGRES_USER` : Your database username (e.g., `admin`)
- `POSTGRES_PASSWORD` : A strong password for the database
- `POSTGRES_DB` : The name of the database (e.g., `canopy_prod`)
- `POSTGRES_EXTERNAL_PORT`: Port exposed on host (default: `5432` or `15432`)

```bash
POSTGRES_USER=my_db_user
POSTGRES_PASSWORD=my_secure_password
POSTGRES_DB=canopy_prod
POSTGRES_EXTERNAL_PORT=15432
```

#### Google SSO (Optional)

To enable Google Sign-In:

- `ACTIVATE_GOOGLE_AUTH`: Set to `True` to enable
- `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret

```bash
ACTIVATE_GOOGLE_AUTH=True
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

#### Domain & Network

- `SITE_ADDRESS` : The public domain name where Canopy will be accessible (e.g., `maps.mycompany.com`). Do not include `http://` or `https://`.

```bash
SITE_ADDRESS=maps.mycompany.com
```

#### Environment

- `ENV` : Set to `prod` for production usage.
- `LOCALE`: Default language (`en` or `fr`)

```bash
ENV=prod
LOCALE=fr
```

## 3. Deployment

Once the `.env.local` file is created and filled with the correct values, run the following command to deploy the application:

```bash
make create-app
```

This command will automatically:

1. Generate an internal `SECRET_KEY` for sessions
2. Build the application
3. Start all services
4. Configure the database

Canopy should now be accessible at `https://<YOUR_SITE_ADDRESS>`.
