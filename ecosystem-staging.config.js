module.exports = {
  apps: [{
    name: 'kyra-backend-staging',
    script: '/home/ubuntu/kyra/backend/.venv/bin/python3',
    args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8002',
    cwd: '/home/ubuntu/kyra/backend',
    interpreter: '/home/ubuntu/kyra/backend/.venv/bin/python3',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'staging',
      PORT: 8002
    },
    error_file: '/home/ubuntu/.pm2/logs/kyra-backend-staging-error.log',
    out_file: '/home/ubuntu/.pm2/logs/kyra-backend-staging-out.log',
    log_file: '/home/ubuntu/.pm2/logs/kyra-backend-staging-combined.log',
    time: true
  }]
} 