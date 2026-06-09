module.exports = {
  apps: [
    {
      name: "xrd-backend",
      script: "python",
      args: "-m uvicorn app:app --reload",
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