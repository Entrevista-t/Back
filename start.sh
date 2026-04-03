#!/bin/bash

clear

# =========================================================
# 🛠️ CONFIGURACIÓ DEL PROJECTE (FastAPI)
# =========================================================
APP_NAME="Entrevistat't Backend"
CONTAINER_DEV="entrevistatt_api_dev"     
CONTAINER_DEBUG="entrevistatt_api_debug"   
API_PORT="8000"                
DEBUG_PORT="5678"

ComposeDev="infra/docker-compose-dev.yml"
ComposeDebug="infra/docker-compose.debug.yml"
MLBaseImage="ghcr.io/entrevista-t/back:ml-base"
MLBaseDockerfile="infra/Dockerfile.ml-base"
# =========================================================

# Definicions de colors
CYAN='\e[36m'
GREEN='\e[32m'
YELLOW='\e[33m'
MAGENTA='\e[35m'
RED='\e[31m'
NC='\e[0m' # No Color (Reset)

echo -e "${CYAN}${APP_NAME} - Docker Manager${NC}"

while true; do
    echo -e "\n${GREEN}----------------------------------------${NC}"
    echo -e "${GREEN}CONTROL MENU${NC}"
    echo -e "${GREEN}----------------------------------------${NC}"
    echo "1. Start/Update environment (Normal mode)"
    echo "2. Start/Update environment (Debug mode with debugpy)"
    echo "3. View live Output (Logs) [Ctrl+C to return]"
    echo "4. Enter container terminal (Bash)"
    echo "5. Run Unit Tests (pytest)"
    echo "6. Stop containers (Stop)"
    echo "7. Build & Push ML base image (GHCR)"
    echo "8. Stop everything and Exit script"
    echo -e "${GREEN}----------------------------------------${NC}"
    
    read -p "Select an option (1-8): " selection

    case $selection in
        1)
            echo -e "${YELLOW}Starting containers in NORMAL MODE...${NC}"
            echo -e "${CYAN}Container name: $CONTAINER_DEV${NC}"
            echo -e "${CYAN}Port: $API_PORT${NC}"
            docker compose -f $ComposeDev up -d --build
            echo -e "${GREEN}Done! Containers running in normal mode.${NC}"
            ;;
        2)
            echo -e "${YELLOW}Starting containers in DEBUG MODE...${NC}"
            echo -e "${CYAN}Container name: $CONTAINER_DEBUG${NC}"
            echo -e "${CYAN}API Port: $API_PORT | Debug Port: $DEBUG_PORT${NC}"
            echo -e "${MAGENTA}Use: Run & Debug (Ctrl+Shift+D) -> 'Python Debugger: FastAPI (Docker Remote)' -> F5${NC}"
            docker compose -f $ComposeDebug up -d --build
            echo -e "${GREEN}Done! Containers running in debug mode. Waiting for debugger connection...${NC}"
            sleep 2
            echo -e "${YELLOW}Opening logs to show debugger status...${NC}"
            docker compose -f $ComposeDebug logs -f api
            ;;
        3)
            echo -e "${YELLOW}Showing logs... (Press Ctrl+C to return to menu)${NC}"
            echo -e "${CYAN}Detecting active mode...${NC}"
            normalRunning=$(docker ps -q -f "name=$CONTAINER_DEV" 2>/dev/null)
            debugRunning=$(docker ps -q -f "name=$CONTAINER_DEBUG" 2>/dev/null)
            
            if [ -n "$debugRunning" ]; then
                echo -e "${MAGENTA}Debug mode container detected${NC}"
                docker compose -f $ComposeDebug logs -f api
            elif [ -n "$normalRunning" ]; then
                echo -e "${GREEN}Normal mode container detected${NC}"
                docker compose -f $ComposeDev logs -f api
            else
                echo -e "${RED}No containers running.${NC}"
            fi
            ;;
        4)
            echo -e "${YELLOW}Connecting to terminal... (Type 'exit' to quit)${NC}"
            echo -e "${CYAN}Detecting active mode...${NC}"
            normalRunning=$(docker ps -q -f "name=$CONTAINER_DEV" 2>/dev/null)
            debugRunning=$(docker ps -q -f "name=$CONTAINER_DEBUG" 2>/dev/null)
            
            if [ -n "$debugRunning" ]; then
                echo -e "${MAGENTA}Connecting to debug mode container...${NC}"
                docker compose -f $ComposeDebug exec api /bin/bash
            elif [ -n "$normalRunning" ]; then
                echo -e "${GREEN}Connecting to normal mode container...${NC}"
                docker compose -f $ComposeDev exec api /bin/bash
            else
                echo -e "${RED}Error: No containers running. Start with option 1 or 2 first.${NC}"
            fi
            ;;
        5)
            echo -e "${CYAN}Running Tests...${NC}"
            docker compose -f $ComposeDev run --rm api pytest || echo -e "${RED}Error running tests.${NC}"
            ;;
        6)
            echo -e "${MAGENTA}Stopping containers...${NC}"
            echo -e "${CYAN}Detecting running containers...${NC}"
            normalRunning=$(docker ps -q -f "name=$CONTAINER_DEV" 2>/dev/null)
            debugRunning=$(docker ps -q -f "name=$CONTAINER_DEBUG" 2>/dev/null)
            
            if [ -n "$debugRunning" ]; then
                echo -e "${MAGENTA}Stopping debug mode container...${NC}"
                docker compose -f $ComposeDebug stop
            fi
            if [ -n "$normalRunning" ]; then
                echo -e "${GREEN}Stopping normal mode container...${NC}"
                docker compose -f $ComposeDev stop
            fi
            if [ -z "$normalRunning" ] && [ -z "$debugRunning" ]; then
                echo -e "${YELLOW}No containers running.${NC}"
            else
                echo -e "${GREEN}Containers stopped.${NC}"
            fi
            ;;
        7)
            echo -e "${YELLOW}Build & Push ML base image to GHCR${NC}"
            echo -e "${CYAN}Image: $MLBaseImage${NC}"
            echo -e "${CYAN}Dockerfile: $MLBaseDockerfile${NC}"

            # Check GHCR login
            loginCheck=$(docker pull ghcr.io/entrevista-t/back:login-test 2>&1)
            if echo "$loginCheck" | grep -qiE "denied|unauthorized"; then
                echo -e "\n${YELLOW}Not logged in to GHCR. Logging in...${NC}"
                echo -e "${MAGENTA}You need a GitHub PAT with 'write:packages' scope.${NC}"
                docker login ghcr.io
                if [ $? -ne 0 ]; then
                    echo -e "${RED}Login failed. Aborting.${NC}"
                    continue
                fi
            fi

            echo -e "\n${YELLOW}Building image...${NC}"
            docker build -t "$MLBaseImage" -f "$MLBaseDockerfile" .
            if [ $? -ne 0 ]; then
                echo -e "${RED}Build failed.${NC}"
                continue
            fi
            echo -e "${GREEN}Build succeeded!${NC}"

            echo -e "${YELLOW}Pushing image to GHCR...${NC}"
            docker push "$MLBaseImage"
            if [ $? -ne 0 ]; then
                echo -e "${RED}Push failed. Make sure you are logged in to GHCR (docker login ghcr.io).${NC}"
                continue
            fi
            echo -e "${GREEN}ML base image pushed successfully!${NC}"
            ;;
        8)
            echo -e "${RED}Shutting down and removing containers...${NC}"
            echo -e "${CYAN}Detecting running containers...${NC}"
            normalRunning=$(docker ps -q -f "name=$CONTAINER_DEV" 2>/dev/null)
            debugRunning=$(docker ps -q -f "name=$CONTAINER_DEBUG" 2>/dev/null)
            
            if [ -n "$debugRunning" ]; then
                echo -e "${MAGENTA}Removing debug mode container...${NC}"
                docker compose -f $ComposeDebug down
            fi
            if [ -n "$normalRunning" ]; then
                echo -e "${GREEN}Removing normal mode container...${NC}"
                docker compose -f $ComposeDev down
            fi
            echo -e "${RED}All containers removed. Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option.${NC}"
            ;;
    esac
done