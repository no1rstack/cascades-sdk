/**
 * Prepares publishable artifacts: mirrored OpenAPI YAML + LICENSE from the SDK repo root.
 * Run via `npm run build` (prepack / prepublishOnly).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const sdkRoot = path.resolve(__dirname, "../..");

const srcYaml = path.join(sdkRoot, "contracts", "api.yaml");
const srcLicense = path.join(sdkRoot, "LICENSE");
const destContracts = path.join(__dirname, "contracts");
const destYaml = path.join(destContracts, "api.yaml");
const destLicense = path.join(__dirname, "LICENSE");

if (!fs.existsSync(srcYaml)) {
  console.error(`Missing mirrored contract: ${srcYaml}`);
  process.exit(1);
}
if (!fs.existsSync(srcLicense)) {
  console.error(`Missing LICENSE at repo root: ${srcLicense}`);
  process.exit(1);
}

fs.mkdirSync(destContracts, { recursive: true });
fs.copyFileSync(srcYaml, destYaml);
fs.copyFileSync(srcLicense, destLicense);
console.log("Build: synced contracts/api.yaml and LICENSE into package tree.");
