import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendTarget =
    env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";

  const apiProxy = {
    target: backendTarget,
    changeOrigin: true,
    secure: false,
    rewrite: (path) => path.replace(/^\/api/, "") || "/",
  };

  return {
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      proxy: {
        "/api": apiProxy,
      },
    },
    preview: {
      host: "0.0.0.0",
      proxy: {
        "/api": apiProxy,
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes("node_modules")) return undefined;
            if (id.includes("recharts")) return "charts";
            if (id.includes("firebase")) return "firebase";
            if (id.includes("framer-motion")) return "motion";
            if (id.includes("react-icons")) return "icons";
            if (id.includes("react-router")) return "router";
            if (id.includes("react-dom") || id.includes("/react/")) return "react";
            return undefined;
          },
        },
      },
    },
  };
});
