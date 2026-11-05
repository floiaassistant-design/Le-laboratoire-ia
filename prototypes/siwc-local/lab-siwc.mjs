// EXP-019 local Electron host: *copy this file and adapter.mjs to the root*
// of the pinned official sign-in-with-chatgpt-devkit checkout, and run with Electron.
// This is deliberately NOT a hosted site or MCP server.
import { app, safeStorage, shell } from "electron";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { createChatGPT } from "@siwc/local";
import { eligibleModels, requestRole } from "./lab-adapter.mjs";

const allowed = new Set(["login", "status", "models", "smoke", "role"]);
const command = process.argv[2];
if (!allowed.has(command)) {
  process.stderr.write(
    "Usage: electron lab-siwc.mjs login|status|models|smoke|role [model] [prompt-file]\n"
  );
  process.exit(2);
}

function getCredentialEncryption() {
  // Never persist an access/refresh token if the OS keyring is unavailable.
  if (!safeStorage.isEncryptionAvailable()
      || (process.platform === "linux"
          && safeStorage.getSelectedStorageBackend?.() === "basic_text")) {
    throw new Error("OS-backed credential encryption is unavailable: no OAuth attempted");
  }
  return {
    id: "electron-safe-storage-v1",
    isAvailable: () => safeStorage.isEncryptionAvailable()
      && !(process.platform === "linux"
        && safeStorage.getSelectedStorageBackend?.() === "basic_text"),
    encrypt: plaintext => new Uint8Array(safeStorage.encryptString(plaintext)),
    decrypt: ciphertext => safeStorage.decryptString(Buffer.from(ciphertext)),
  };
}

async function main() {
  app.setName("Laboratoire IA SIWC");
  await app.whenReady();
  const client = createChatGPT({
    appName: "Laboratoire IA SIWC",
    appId: "laboratoire-ia-siwc",
    redirectPort: 0,
    storageDir: join(app.getPath("userData"), "laboratoire-ia-siwc"),
    credentialEncryption: getCredentialEncryption(),
    sendHostId: true,
    openBrowser: async url => {
      const parsed = new URL(url);
      if (parsed.origin !== "https://auth.openai.com") {
        throw new Error("Unexpected authentication URL: refusing to open browser");
      }
      await shell.openExternal(parsed.href);
    },
  });
  if (command === "login") {
    const result = await client.signIn(); // explicit user browser consent required
    process.stdout.write(JSON.stringify({
      connected: result.status === "connected",
      plan_usage_enabled: result.sharing === true,
      message: result.sharing
        ? "Eligible plan permission reported; use models, then smoke"
        : "No plan permission reported; no inference will be performed",
    }) + "\n");
    return;
  }
  if (command === "status") {
    const state = await client.getSession();
    process.stdout.write(JSON.stringify({
      connected: state.status === "connected", plan_usage_enabled: state.sharing,
    }) + "\n");
    return;
  }
  const models = await eligibleModels(client);
  if (command === "models") {
    process.stdout.write(JSON.stringify(models.map(m => ({
      slug: m.slug, name: m.displayName,
    })), null, 2) + "\n");
    return;
  }
  if (command === "smoke") {
    // Exactly one opt-in Responses request, billed against eligible plan usage.
    const model = models[0]?.slug;
    if (!model) throw new Error("No available model; no request sent");
    const output = await requestRole(client, {
      model, prompt: "Reply with exactly: Laboratory connection works.",
    });
    process.stdout.write(JSON.stringify({
      model: output.model, output: output.text,
      real_request_completed: true, historical_chat_access: false,
    }) + "\n");
    return;
  }
  // Role requires explicit model selection; no hidden default model.
  const model = process.argv[3];
  const filename = process.argv[4];
  if (!model || !filename || process.argv.length !== 5) {
    throw new Error("Usage: electron lab-siwc.mjs role <catalog-model-slug> <prompt.txt>");
  }
  const file = await readFile(filename);
  if (file.length > 16_000) throw new Error("Prompt file too large");
  const output = await requestRole(client, { model, prompt: file.toString("utf8") });
  // Output contains experiment text, not auth credentials. Redirect to a
  // gitignored file and *never* copy unredacted experiment logs into GitHub.
  process.stdout.write(JSON.stringify(output) + "\n");
}

// Electron's ESM main entry must finish evaluating before the app's "ready"
// event is dispatched. A top-level `await main()` deadlocks because main()
// awaits app.whenReady(). Start the Promise chain without awaiting it here.
void main()
  .catch(error => {
    // Do not print raw HTTP responses, access tokens or stack dumps.
    // Error messages can contain request details. Never print raw SDK errors or tokens.
    const code = error && typeof error.code === "string"
      && /^[a-z_]{1,50}$/.test(error.code) ? error.code : "request_failed";
    process.stderr.write("EXP-019 not completed (" + code + "). No real success recorded.\n");
    process.exitCode = 1;
  })
  .finally(() => {
    app.quit();
  });
