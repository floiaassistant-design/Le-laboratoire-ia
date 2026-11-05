import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { checkModels, validatePrompt, eligibleModels, requestRole } from "./adapter.mjs";

const fake = ({ sharing = true, models = [{ slug: "test-local-model", displayName: "Mock" }],
                answer = "FINAL: 7" } = {}) => {
  const calls = [];
  return {
    calls,
    async getSession() { calls.push("session"); return {status:"connected", sharing}; },
    async listModels() { calls.push("catalog"); return models; },
    async streamResponse(options) { calls.push(options); return {text: answer}; },
  };
};

test("denies inference when sharing is not explicitly authorized", async () => {
  const c = fake({sharing:false});
  await assert.rejects(() => requestRole(c, {model:"test-local-model",prompt:"question"}), /not authorized/);
  assert.deepEqual(c.calls, ["session"]);
});
test("allows no invented model, even with valid plan sharing", async () => {
  const c = fake();
  await assert.rejects(() => requestRole(c, {model:"not-in-catalog",prompt:"question"}), /not available/);
  assert.equal(c.calls.filter(x => typeof x === "object").length, 0);
});
test("requires explicit model and nonempty prompt", async () => {
  const c = fake();
  await assert.rejects(() => requestRole(c, {prompt:"question"}), /explicit model/);
  await assert.rejects(() => requestRole(c, {model:"test-local-model",prompt:""}), /Prompt/);
  await assert.rejects(() => requestRole(c, {model:"test-local-model",prompt:"x".repeat(8001)}), /Prompt/);
  assert.equal(c.calls.filter(x => typeof x === "object").length, 0);
});
test("sends one fresh response with only supplied input; no prior context", async () => {
  const c = fake();
  const out = await requestRole(c, {model:"test-local-model",prompt:"question only"});
  assert.deepEqual(c.calls.filter(x => typeof x === "object"), [
    {model:"test-local-model", input:"question only"},
  ]);
  assert.equal(out.text, "FINAL: 7");
  assert.equal(out.prior_context_sent, false);
  assert.equal(out.independence_verified, false);
  assert.equal(out.source, "siwc_local_responses_api");
});
test("empty completed response is not counted as observed success", async () => {
  await assert.rejects(() => requestRole(fake({answer:"  "}),
    {model:"test-local-model",prompt:"question"}), /nonempty/);
});
test("catalog and input format checks guard the client", async () => {
  assert.equal(checkModels([{slug:"model-a"}], "model-a"), "model-a");
  assert.throws(() => checkModels([{slug:"model-a"}], "wrong model"), /not available/);
  assert.throws(() => checkModels([{slug:3}], ""), /catalog/);
  assert.throws(() => checkModels([], ""), /No eligible model/);
  assert.equal(validatePrompt("question"), "question");
  assert.throws(() => validatePrompt("hello\u0000oops"), /Prompt/);
  await assert.rejects(() => eligibleModels({}), /compatible/);
});
test("not connected is a hard stop", async () => {
  let invoked = false;
  const client = {
    async getSession() { return {status:"reauth_required",sharing:true}; },
    async listModels() { invoked = true; return [{slug:"model-a"}]; },
    async streamResponse() { invoked = true; return {text:"FINAL: 1"}; },
  };
  await assert.rejects(() => requestRole(client,{model:"model-a",prompt:"question"}), /not authorized/);
  assert.equal(invoked,false);
});

test("Electron ESM launcher must not deadlock its own ready event", async () => {
  const source = await readFile(new URL("./lab-siwc.mjs", import.meta.url), "utf8");
  assert.match(source, /await app\.whenReady\(\)/);
  assert.match(source, /void main\(\)\s*\.catch\(/);
  assert.doesNotMatch(source, /^\s*await main\(\)/m);
});
