import { defineRailway, github, postgres, project, service } from "railway/iac";

export default defineRailway(() => {
  const database = postgres("postgres");

  const backend = service("backend", {
    source: github("jems0906/GameNight-NOC", {
      branch: "main",
      rootDirectory: "backend",
    }),
    healthcheck: "/api/health",
    env: {
      DATABASE_URL: database.env.DATABASE_URL,
      CORS_ORIGINS: "https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}",
    },
  });

  const frontend = service("frontend", {
    source: github("jems0906/GameNight-NOC", {
      branch: "main",
      rootDirectory: "frontend",
    }),
    healthcheck: "/",
    env: {
      VITE_API_URL: "https://${{backend.RAILWAY_PUBLIC_DOMAIN}}",
    },
  });

  return project("GameNight-NOC", {
    resources: [database, backend, frontend],
  });
});
