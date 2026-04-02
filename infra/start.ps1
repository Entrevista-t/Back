# start.ps1
Clear-Host

# Ensure we run from the repo root (parent of infra/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ScriptDir)

# =========================================================
# 🛠️ CONFIGURACIÓN DEL PROYECTO (FastAPI)
# =========================================================
$APP_NAME        = "Entrevistat't Backend"
$CONTAINER_DEV   = "entrevistatt_api_dev"     
$CONTAINER_DEBUG = "entrevistatt_api_debug"   
$API_PORT        = "8000"                
$DEBUG_PORT      = "5678"

$ComposeDev      = "infra/docker-compose-dev.yml"
$ComposeDebug    = "infra/docker-compose.debug.yml"
$MLBaseImage     = "ghcr.io/entrevista-t/back:ml-base"
$MLBaseDockerfile = "infra/Dockerfile.ml-base"
# =========================================================

Write-Host "$APP_NAME - Docker Manager" -ForegroundColor Cyan

while ($true) {
    Write-Host "`n----------------------------------------" -ForegroundColor Green
    Write-Host "CONTROL MENU" -ForegroundColor Green
    Write-Host "----------------------------------------"
    Write-Host "1. Start/Update environment (Normal mode)"
    Write-Host "2. Start/Update environment (Debug mode with debugpy)"
    Write-Host "3. View live Output (Logs) [Ctrl+C to return]"
    Write-Host "4. Enter container terminal (Bash)"
    Write-Host "5. Run Unit Tests (pytest)"
    Write-Host "6. Stop containers (Stop)"
    Write-Host "7. Build & Push ML base image (GHCR)"
    Write-Host "8. Stop everything and Exit script"
    Write-Host "----------------------------------------"
    
    $selection = Read-Host "Select an option (1-8)"

    switch ($selection) {
        "1" {
            Write-Host "Starting containers in NORMAL MODE..." -ForegroundColor Yellow
            Write-Host "Container name: $CONTAINER_DEV" -ForegroundColor Cyan
            Write-Host "Port: $API_PORT" -ForegroundColor Cyan
            docker compose -f $ComposeDev up -d --build
            Write-Host "Done! Containers running in normal mode." -ForegroundColor Green
        }
        "2" {
            Write-Host "Starting containers in DEBUG MODE..." -ForegroundColor Yellow
            Write-Host "Container name: $CONTAINER_DEBUG" -ForegroundColor Cyan
            Write-Host "API Port: $API_PORT | Debug Port: $DEBUG_PORT" -ForegroundColor Cyan
            Write-Host "Use: Run & Debug (Ctrl+Shift+D) -> 'Python Debugger: FastAPI (Docker Remote)' -> F5" -ForegroundColor Magenta
            docker compose -f $ComposeDebug up -d --build
            Write-Host "Done! Containers running in debug mode. Waiting for debugger connection..." -ForegroundColor Green
            Start-Sleep -Seconds 2
            Write-Host "Opening logs to show debugger status..." -ForegroundColor Yellow
            docker compose -f $ComposeDebug logs -f api
        }
        "3" {
            Write-Host "Showing logs... (Press Ctrl+C to return to menu)" -ForegroundColor Yellow
            Write-Host "Detecting active mode..." -ForegroundColor Cyan
            $normalRunning = docker ps -q -f "name=$CONTAINER_DEV" 2>$null
            $debugRunning = docker ps -q -f "name=$CONTAINER_DEBUG" 2>$null
            
            if ($debugRunning) {
                Write-Host "Debug mode container detected" -ForegroundColor Magenta
                docker compose -f $ComposeDebug logs -f api
            } elseif ($normalRunning) {
                Write-Host "Normal mode container detected" -ForegroundColor Green
                docker compose -f $ComposeDev logs -f api
            } else {
                Write-Host "No containers running." -ForegroundColor Red
            }
        }
        "4" {
            Write-Host "Connecting to terminal... (Type 'exit' to quit)" -ForegroundColor Yellow
            Write-Host "Detecting active mode..." -ForegroundColor Cyan
            $normalRunning = docker ps -q -f "name=$CONTAINER_DEV" 2>$null
            $debugRunning = docker ps -q -f "name=$CONTAINER_DEBUG" 2>$null
            
            try {
                if ($debugRunning) {
                    Write-Host "Connecting to debug mode container..." -ForegroundColor Magenta
                    docker compose -f $ComposeDebug exec api /bin/bash
                } elseif ($normalRunning) {
                    Write-Host "Connecting to normal mode container..." -ForegroundColor Green
                    docker compose -f $ComposeDev exec api /bin/bash
                } else {
                    Write-Host "Error: No containers running. Start with option 1 or 2 first." -ForegroundColor Red
                }
            } catch {
                Write-Host "Error: Cannot connect to container." -ForegroundColor Red
            }
        }
        "5" {
            Write-Host "Running Tests..." -ForegroundColor Cyan
            try {
                docker compose -f $ComposeDev run --rm api pytest
            } catch {
                Write-Host "Error running tests." -ForegroundColor Red
            }
        }
        "6" {
            Write-Host "Stopping containers..." -ForegroundColor Magenta
            Write-Host "Detecting running containers..." -ForegroundColor Cyan
            $normalRunning = docker ps -q -f "name=$CONTAINER_DEV" 2>$null
            $debugRunning = docker ps -q -f "name=$CONTAINER_DEBUG" 2>$null
            
            if ($debugRunning) {
                Write-Host "Stopping debug mode container..." -ForegroundColor Magenta
                docker compose -f $ComposeDebug stop
            }
            if ($normalRunning) {
                Write-Host "Stopping normal mode container..." -ForegroundColor Green
                docker compose -f $ComposeDev stop
            }
            if (-not $normalRunning -and -not $debugRunning) {
                Write-Host "No containers running." -ForegroundColor Yellow
            } else {
                Write-Host "Containers stopped." -ForegroundColor Green
            }
        }
        "7" {
            Write-Host "Build & Push ML base image to GHCR" -ForegroundColor Yellow
            Write-Host "Image: $MLBaseImage" -ForegroundColor Cyan
            Write-Host "Dockerfile: $MLBaseDockerfile" -ForegroundColor Cyan

            # Check GHCR login
            $loginCheck = docker pull ghcr.io/entrevista-t/back:login-test 2>&1
            if ($loginCheck -match "denied|unauthorized") {
                Write-Host "`nNot logged in to GHCR. Logging in..." -ForegroundColor Yellow
                Write-Host "You need a GitHub PAT with 'write:packages' scope." -ForegroundColor Magenta
                docker login ghcr.io
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "Login failed. Aborting." -ForegroundColor Red
                    continue
                }
            }

            Write-Host "`nBuilding image..." -ForegroundColor Yellow
            docker build -t $MLBaseImage -f $MLBaseDockerfile .
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Build failed." -ForegroundColor Red
                continue
            }
            Write-Host "Build succeeded!" -ForegroundColor Green

            Write-Host "Pushing image to GHCR..." -ForegroundColor Yellow
            docker push $MLBaseImage
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Push failed. Make sure you are logged in to GHCR (docker login ghcr.io)." -ForegroundColor Red
                continue
            }
            Write-Host "ML base image pushed successfully!" -ForegroundColor Green
        }
        "8" {
            Write-Host "Shutting down and removing containers..." -ForegroundColor Red
            Write-Host "Detecting running containers..." -ForegroundColor Cyan
            $normalRunning = docker ps -q -f "name=$CONTAINER_DEV" 2>$null
            $debugRunning = docker ps -q -f "name=$CONTAINER_DEBUG" 2>$null
            
            if ($debugRunning) {
                Write-Host "Removing debug mode container..." -ForegroundColor Magenta
                docker compose -f $ComposeDebug down
            }
            if ($normalRunning) {
                Write-Host "Removing normal mode container..." -ForegroundColor Green
                docker compose -f $ComposeDev down
            }
            Write-Host "All containers removed. Exiting..." -ForegroundColor Red
            exit
        }
        Default {
            Write-Host "Invalid option." -ForegroundColor Red
        }
    }
}