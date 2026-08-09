import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "../../packages/contracts/openapi.json",
  output: {
    path: "lib/api/generated",
    postProcess: ["prettier"],
  },
  plugins: ["@hey-api/typescript"],
});
