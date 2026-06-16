/** PM2 极简部署：后端 API + 前端，无需 Supervisor / Celery / Redis */
module.exports = {
  apps: [
    {
      name: "edu-policy-api",
      cwd: "./backend",
      script: ".venv/bin/uvicorn",
      args: "app.main:app --host 127.0.0.1 --port 8000 --workers 1",
      interpreter: "none",
      autorestart: true,
      max_memory_restart: "400M",
    },
    {
      name: "edu-policy-web",
      cwd: "./frontend",
      script: "npm",
      args: "start -- -p 3000",
      interpreter: "none",
      autorestart: true,
      max_memory_restart: "400M",
    },
  ],
};
