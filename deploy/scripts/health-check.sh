#!/bin/bash

# Health check script for Kyra Health Assistant environments
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check endpoint health
check_endpoint() {
    local url=$1
    local name=$2
    local timeout=10
    
    echo -n "🔍 Checking $name ($url)... "
    
    if curl -f -s --max-time $timeout "$url/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ UNHEALTHY${NC}"
        return 1
    fi
}

# Function to check PM2 process
check_pm2() {
    local name=$1
    local display_name=$2
    
    echo -n "⚡ Checking PM2 process $display_name... "
    
    if pm2 describe "$name" > /dev/null 2>&1; then
        local status=$(pm2 jlist | jq -r ".[] | select(.name == \"$name\") | .pm2_env.status")
        if [ "$status" = "online" ]; then
            echo -e "${GREEN}✅ RUNNING${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  STATUS: $status${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ NOT FOUND${NC}"
        return 1
    fi
}

# Function to check nginx
check_nginx() {
    echo -n "🌐 Checking nginx service... "
    
    if sudo systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✅ RUNNING${NC}"
        return 0
    else
        echo -e "${RED}❌ STOPPED${NC}"
        return 1
    fi
}

# Function to check disk space
check_disk() {
    echo -n "💾 Checking disk space... "
    
    local usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$usage" -lt 80 ]; then
        echo -e "${GREEN}✅ OK (${usage}% used)${NC}"
        return 0
    elif [ "$usage" -lt 90 ]; then
        echo -e "${YELLOW}⚠️  WARNING (${usage}% used)${NC}"
        return 1
    else
        echo -e "${RED}❌ CRITICAL (${usage}% used)${NC}"
        return 1
    fi
}

# Function to check memory usage
check_memory() {
    echo -n "🧠 Checking memory usage... "
    
    local usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$usage" -lt 80 ]; then
        echo -e "${GREEN}✅ OK (${usage}% used)${NC}"
        return 0
    elif [ "$usage" -lt 90 ]; then
        echo -e "${YELLOW}⚠️  WARNING (${usage}% used)${NC}"
        return 1
    else
        echo -e "${RED}❌ CRITICAL (${usage}% used)${NC}"
        return 1
    fi
}

echo "🏥 Kyra Health Assistant - Health Check Report"
echo "================================================"
echo ""

# Initialize counters
healthy=0
total=0

# Check system services
echo "🔧 System Services:"
echo "-------------------"
check_nginx && ((healthy++)) || true
((total++))
check_disk && ((healthy++)) || true
((total++))
check_memory && ((healthy++)) || true
((total++))
echo ""

# Check PM2 processes
echo "⚡ Backend Processes:"
echo "---------------------"
check_pm2 "kyra-backend" "Production" && ((healthy++)) || true
((total++))
check_pm2 "kyra-backend-staging" "Staging" && ((healthy++)) || true
((total++))
check_pm2 "kyra-backend-dev" "Development" && ((healthy++)) || true
((total++))
echo ""

# Check endpoints
echo "🌐 Endpoint Health:"
echo "-------------------"
check_endpoint "https://demo.kyrahealth.ai/healthz" "Production" && ((healthy++)) || true
((total++))
check_endpoint "https://staging.kyrahealth.ai" "Staging" && ((healthy++)) || true
((total++))
check_endpoint "https://dev.kyrahealth.ai" "Development" && ((healthy++)) || true
((total++))
echo ""

# Summary
echo "📊 Health Summary:"
echo "------------------"
local percentage=$((healthy * 100 / total))
echo "Overall Health: $healthy/$total endpoints healthy ($percentage%)"

if [ $percentage -eq 100 ]; then
    echo -e "${GREEN}🎉 All systems operational!${NC}"
    exit 0
elif [ $percentage -ge 80 ]; then
    echo -e "${YELLOW}⚠️  Minor issues detected${NC}"
    exit 1
else
    echo -e "${RED}🚨 Critical issues detected${NC}"
    exit 2
fi 