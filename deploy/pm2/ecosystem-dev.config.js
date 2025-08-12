module.exports = {
  apps: [{
    name: 'kyra-backend-dev',
    script: 'uvicorn',
    args: 'app.main:app --host 0.0.0.0 --port 8003',
    cwd: '/home/ubuntu/kyra/backend',
    interpreter: '/home/ubuntu/kyra/backend/.venv/bin/python',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'development',
      PORT: 8003
    },
    error_file: '/home/ubuntu/.pm2/logs/kyra-backend-dev-error.log',
    out_file: '/home/ubuntu/.pm2/logs/kyra-backend-dev-out.log',
    log_file: '/home/ubuntu/.pm2/logs/kyra-backend-dev-combined.log',
    time: true
  }]
} 