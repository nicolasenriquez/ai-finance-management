import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), "");
    var proxyTarget = env.VITE_PROXY_TARGET || "http://localhost:8123";
    return {
        plugins: [react()],
        server: {
            host: "0.0.0.0",
            port: 3000,
            proxy: {
                "/api": {
                    target: proxyTarget,
                    changeOrigin: true,
                },
            },
        },
    };
});
