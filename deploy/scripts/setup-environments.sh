#!/bin/bash

# Setup script for staging and development environments
set -e

echo "🚀 Setting up Kyra Health Assistant environments..."

# Create directories
echo "📁 Creating directories..."
sudo mkdir -p /var/www/kyra-staging
sudo mkdir -p /var/www/kyra-dev

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R ubuntu:ubuntu /var/www/kyra-staging
sudo chown -R ubuntu:ubuntu /var/www/kyra-dev
sudo chmod -R 755 /var/www/kyra-staging
sudo chmod -R 755 /var/www/kyra-dev

# Copy nginx configurations
echo "🌐 Setting up nginx configurations..."
sudo cp deploy/nginx/kyra-staging.conf /etc/nginx/sites-available/
sudo cp deploy/nginx/kyra-dev.conf /etc/nginx/sites-available/

# Enable sites
sudo ln -sf /etc/nginx/sites-available/kyra-staging.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/kyra-dev.conf /etc/nginx/sites-enabled/

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

# Create PM2 ecosystem files
echo "⚡ Setting up PM2 configurations..."
cp deploy/pm2/ecosystem-staging.config.js ecosystem-staging.config.js
cp deploy/pm2/ecosystem-dev.config.js ecosystem-dev.config.js

echo "✅ Environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Add DNS records for staging.kyrahealth.ai and dev.kyrahealth.ai"
echo "2. Get SSL certificates: sudo certbot --nginx -d staging.kyrahealth.ai -d dev.kyrahealth.ai"
echo "3. Start staging backend: pm2 start ecosystem-staging.config.js"
echo "4. Start dev backend: pm2 start ecosystem-dev.config.js"
echo "5. Reload nginx: sudo systemctl reload nginx"
echo ""
echo "🌐 Your environments will be available at:"
echo "   Production: https://kyrahealth.ai"
echo "   Staging: https://staging.kyrahealth.ai"
echo "   Development: https://dev.kyrahealth.ai" 