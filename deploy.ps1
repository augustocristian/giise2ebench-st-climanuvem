<#
.SYNOPSIS
    Convenience wrapper to deploy the ClimaNuvem SUT (sut/backend + sut/frontend) locally.

.DESCRIPTION
    Prerequisites (see sut/README.md for full detail):
      - Docker + Docker Compose for the backend
      - Node.js 22 + npm for the frontend
      - sut/backend/.env with POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, OLLAMA_MODEL
      - sut/backend/secrets/firebase_key.json (Firebase Admin credentials)
      - sut/frontend/.env with EXPO_PUBLIC_* variables

.PARAMETER Target
    One of: backend, frontend, all, down

.PARAMETER Detach
    When deploying the backend, run docker compose in detached mode.

.PARAMETER Volumes
    With target 'down', also remove volumes (Postgres data + Ollama models). Destructive.

.EXAMPLE
    ./deploy.ps1 backend
.EXAMPLE
    ./deploy.ps1 frontend
.EXAMPLE
    ./deploy.ps1 all
.EXAMPLE
    ./deploy.ps1 down -Volumes
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("backend", "frontend", "all", "down")]
    [string]$Target,

    [switch]$Detach,

    [switch]$Volumes
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "sut/backend"
$FrontendDir = Join-Path $RootDir "sut/frontend"

function Deploy-Backend {
    param([switch]$AsDetached)

    $envFile = Join-Path $BackendDir ".env"
    if (-not (Test-Path $envFile)) {
        Write-Error "ERROR: $envFile not found. Create it with POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, OLLAMA_MODEL (see sut/README.md)."
        exit 1
    }

    $firebaseKey = Join-Path $BackendDir "secrets/firebase_key.json"
    if (-not (Test-Path $firebaseKey)) {
        Write-Warning "$firebaseKey not found. Firebase-authenticated requests will fail until it is provided."
    }

    Write-Host "==> Starting backend (PostgreSQL, Ollama, FastAPI) via Docker Compose"
    Push-Location $BackendDir
    try {
        if ($AsDetached) {
            docker compose up --build -d
        } else {
            docker compose up --build
        }
    } finally {
        Pop-Location
    }
}

function Stop-Backend {
    param([switch]$RemoveVolumes)

    Write-Host "==> Stopping backend (Docker Compose)"
    Push-Location $BackendDir
    try {
        if ($RemoveVolumes) {
            Write-Host "==> Also removing volumes (Postgres data + Ollama models will be deleted)"
            docker compose down --volumes
        } else {
            docker compose down
        }
    } finally {
        Pop-Location
    }
}

function Deploy-Frontend {
    $envFile = Join-Path $FrontendDir ".env"
    if (-not (Test-Path $envFile)) {
        Write-Warning "$envFile not found. Create it with EXPO_PUBLIC_BACKEND_URL and EXPO_PUBLIC_FIREBASE_* variables (see sut/README.md)."
    }

    Write-Host "==> Installing frontend dependencies"
    Push-Location $FrontendDir
    try {
        npm install
        Write-Host "==> Starting Expo dev server"
        npm start
    } finally {
        Pop-Location
    }
}

switch ($Target) {
    "backend" {
        Deploy-Backend -AsDetached:$Detach
    }
    "frontend" {
        Deploy-Frontend
    }
    "all" {
        Deploy-Backend -AsDetached
        Write-Host "==> Backend started in the background. Tail logs with: cd sut/backend; docker compose logs -f"
        Deploy-Frontend
    }
    "down" {
        Stop-Backend -RemoveVolumes:$Volumes
    }
}
