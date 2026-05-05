import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** Absolute path to the bundled OpenAPI 3 YAML contract shipped with this package. */
export const apiYamlPath = path.join(__dirname, "contracts", "api.yaml");

/** Install root of this package (for custom tooling). */
export const packageRoot = __dirname;
