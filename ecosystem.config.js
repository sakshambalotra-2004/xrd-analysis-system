module.exports = {
  apps: [
    {
      name: "xrd-backend",
      script: "python",
      args: "-m uvicorn app:app --host 0.0.0.0 --port 8000",
      cwd: "./backend",
      interpreter: "none",
    },
    {
      name: "xrd-frontend",
      script: "cmd",
      args: "/c npm run dev",
      cwd: "./frontend",
      interpreter: "none",
    },
  ],
};