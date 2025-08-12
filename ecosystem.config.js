module.exports = {
  apps: [{
    name: 'kyra-backend',
    script: '/home/ubuntu/kyra/backend/venv/bin/python3',
    args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8001',
    cwd: '/home/ubuntu/kyra/backend',
    env: {
      NODE_ENV: 'production',
      PYTHONPATH: '/home/ubuntu/kyra/backend'
    },
    instances: 1,
    exec_mode: 'fork'
  }]
}
