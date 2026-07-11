import { defineConfig } from "vitest/config";

export default defineConfig({
  build: { sourcemap: true },
  test: { environment: "node", exclude: ["e2e/**", "node_modules/**"] },
});
