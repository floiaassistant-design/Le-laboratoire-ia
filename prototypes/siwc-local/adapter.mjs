// EXP-019: pure validation and injected runtime; tests never call a real model.
// Sign-in, token storage and network transport belong to @siwc/local (official DevKit).
export function checkModels(models, requestedModel) {
  if (!Array.isArray(models) || models.some(m => !m || typeof m.slug !== "string")) {
    throw new Error("Invalid model catalog");
  }
  if (requestedModel && (!/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$/.test(requestedModel)
      || !models.some(model => model.slug === requestedModel))) {
    throw new Error("Requested model is not available in the authenticated catalog");
  }
  const chosen = requestedModel || models[0]?.slug;
  if (!chosen) throw new Error("No eligible model is available for this account");
  return chosen;
}

export function validatePrompt(text) {
  if (typeof text !== "string" || !text.trim() || text.length > 8_000
      || text.includes("\u0000")) {
    throw new Error("Prompt must contain 1..8000 characters and no NUL");
  }
  return text;
}

export async function eligibleModels(client) {
  if (!client || typeof client.getSession !== "function"
      || typeof client.listModels !== "function") {
    throw new TypeError("A compatible SIWC client is required");
  }
  const session = await client.getSession();
  if (session?.status !== "connected" || session.sharing !== true) {
    throw new Error("ChatGPT plan usage is not authorized; sign in and approve sharing");
  }
  return client.listModels();
}

export async function requestRole(client, { model, prompt }) {
  const input = validatePrompt(prompt);
  // Require a selected catalog slug: no silent model substitution.
  if (typeof model !== "string" || !model) throw new Error("Choose an explicit model");
  const catalog = await eligibleModels(client);
  const slug = checkModels(catalog, model);
  // Each request has just the current prompt. No response IDs or prior chat passed.
  const reply = await client.streamResponse({ model: slug, input });
  if (!reply || typeof reply.text !== "string" || !reply.text.trim()) {
    throw new Error("No completed nonempty model output");
  }
  return {
    model: slug, text: reply.text,
    status: "real_response_reported_by_sdk",
    prior_context_sent: false,
    independence_verified: false,
    source: "siwc_local_responses_api",
  };
}
