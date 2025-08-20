# Kyra Deployment Guide

## Environment Overview
- **Production**: `https://demo.kyrahealth.ai` (Port 8001)
- **Staging**: `https://staging.kyrahealth.ai` (Port 8002)
- **Development**: `https://dev.kyrahealth.ai` (Port 8003)

## 📁 Directory Structure

```
deploy/
├── environments/          # Environment-specific configs
│   ├── production.env
│   ├── staging.env
│   └── development.env
├── nginx/                # Nginx configurations
│   ├── kyra-staging.conf
│   └── kyra-dev.conf
├── pm2/                  # PM2 ecosystem configs
│   ├── ecosystem-staging.config.js
│   └── ecosystem-dev.config.js
├── scripts/              # Deployment and health check scripts
│   ├── setup-environments.sh
│   └── health-check.sh
└── README.md
```

## 🚀 Quick Setup

### 1. Initial Environment Setup

```bash
# Run the setup script
./deploy/scripts/setup-environments.sh
```

### 2. DNS Configuration

Add these DNS records to your domain provider:

```
Type: A
Name: staging
Value: [YOUR_SERVER_IP]
TTL: 300

Type: A
Name: dev
Value: [YOUR_SERVER_IP]
TTL: 300
```

### 3. SSL Certificates

```bash
# Get SSL certificates for staging and dev
sudo certbot --nginx -d demo.kyrahealth.ai -d staging.kyrahealth.ai -d dev.kyrahealth.ai
```

### 4. Start Backend Services

```bash
# Start staging backend
pm2 start ecosystem-staging.config.js

# Start development backend
pm2 start ecosystem-dev.config.js

# Save PM2 configuration
pm2 save
```

### 5. Reload Nginx

```bash
sudo systemctl reload nginx
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The `.github/workflows/ci-cd.yml` file automatically:

1. **Tests** frontend and backend code
2. **Builds** frontend assets
3. **Deploys** to staging on `develop` branch commits
4. **Deploys** to production on `main` branch commits
5. **Health checks** all environments after deployment

### Required GitHub Secrets

Add these secrets to your GitHub repository:

```
STAGING_HOST: [YOUR_SERVER_IP]
STAGING_USERNAME: ubuntu
STAGING_SSH_KEY: [YOUR_SSH_PRIVATE_KEY]

PRODUCTION_HOST: [YOUR_SERVER_IP]
PRODUCTION_USERNAME: ubuntu
PRODUCTION_SSH_KEY: [YOUR_SSH_PRIVATE_KEY]
```

## 🏥 Health Monitoring

### Manual Health Check

```bash
# Run comprehensive health check
./deploy/scripts/health-check.sh
```

### Automated Health Checks

- **Endpoint Health**: `/health` endpoints on all environments
- **Process Monitoring**: PM2 process status
- **System Resources**: Disk space, memory usage
- **Service Status**: Nginx, PM2 processes

## 📊 Deployment Flow

```
Feature Branch → Develop Branch → Staging → Main Branch → Production
     ↓              ↓              ↓           ↓           ↓
   Local Dev    Auto Deploy    Testing    Auto Deploy   Live Users
```

### Branch Strategy

- **`main`**: Production-ready code, auto-deploys to production
- **`develop`**: Integration branch, auto-deploys to staging
- **`feature/*`**: Individual features, no auto-deployment

## 🛠️ Manual Deployment

### Frontend Deployment

```bash
# Build and deploy to specific environment
cd frontend
npm run build

# Deploy to staging
sudo rm -rf /var/www/kyra-staging/*
sudo cp -r dist/* /var/www/kyra-staging/
sudo chown -R www-data:www-data /var/www/kyra-staging/

# Deploy to development
sudo rm -rf /var/www/kyra-dev/*
sudo cp -r dist/* /var/www/kyra-dev/
sudo chown -R www-data:www-data /var/www/kyra-dev/
```

### Backend Deployment

```bash
# Update backend code
cd backend
git pull origin [branch]
source .venv/bin/activate
pip install -r requirements.txt

# Restart specific environment
pm2 restart ecosystem-staging.config.js  # Staging
pm2 restart ecosystem-dev.config.js      # Development
pm2 restart ecosystem.config.js          # Production
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 8001, 8002, 8003 are available
2. **Permission Issues**: Check file ownership and nginx permissions
3. **SSL Errors**: Verify certificate paths and nginx configuration
4. **PM2 Issues**: Check logs with `pm2 logs [process-name]`

### Log Locations

- **PM2 Logs**: `~/.pm2/logs/`
- **Nginx Logs**: `/var/log/nginx/`
- **Application Logs**: Check PM2 process logs

### Health Check Failures

- **Endpoint Unhealthy**: Check backend process and nginx config
- **Process Not Found**: Verify PM2 configuration and process names
- **High Resource Usage**: Monitor disk space and memory

## 📈 Monitoring & Alerts

### Health Check Cron Job

```bash
# Add to crontab for automated monitoring
*/5 * * * * /home/ubuntu/kyra/deploy/scripts/health-check.sh >> /var/log/kyra-health.log 2>&1
```

### Alerting

- **Email Alerts**: Configure in health check script
- **Slack/Discord**: Webhook integration
- **SMS**: Emergency contact alerts

## 🔐 Security Considerations

- **Environment Isolation**: Separate databases and configurations
- **Access Control**: Restrict staging/dev access as needed
- **SSL/TLS**: All environments use HTTPS
- **Firewall**: Configure server firewall appropriately

## 📚 Additional Resources

- [Nginx Configuration](https://nginx.org/en/docs/)
- [PM2 Process Manager](https://pm2.keymetrics.io/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Let's Encrypt SSL](https://letsencrypt.org/docs/)

---

**Need Help?** Check the logs, run health checks, and ensure all services are running properly. 