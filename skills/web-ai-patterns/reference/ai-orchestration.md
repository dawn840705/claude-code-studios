# Reference: AI Orchestration & i18n-Safe Parsing Patterns

Reusable patterns for LLM-orchestration and internationalized output parsing in web+AI (SaaS) products.

Field-proven source: **SpecForge** (Next.js + Firebase + Claude API + PortOne). The patterns below are generalized — the concrete file paths cited are the original implementation, but each pattern applies to any web+AI stack (any streaming HTTP framework, any LLM provider with tool-use, any multi-locale product).

Each pattern: **Problem → Approach → Core snippet → When to apply / Caveats.**

---

## 1. SSE streaming orchestrator + Tool-Use pipeline

**Problem**: An LLM orchestrator calls several sub-agents sequentially/conditionally in a multi-stage pipeline, and you want the user to see progress in real time. The UI must distinguish each stage (plan / start / result / done / error) to render them differently.

**Approach**:
- The server opens a single `ReadableStream` for SSE and emits **typed events** as JSON. Send `{ type, ... }` structures rather than raw text deltas, so the UI can branch by state.
- Expose sub-agents to the orchestrator LLM **as tools** (`call_xxx`). Loop while `stop_reason === "tool_use"`: actually execute each tool, feed the result back as a `tool_result`, and let the LLM decide the next step. Stop on `end_turn`.
- Implement conditional blocking by **filtering the tool list itself** (e.g. remove a specific tool in a given state). Removing the *means* an LLM can use is safer than prompting "don't call X".

**Core snippet**:
```ts
function sseEvent(data: object): string { return `data: ${JSON.stringify(data)}\n\n`; }

const stream = new ReadableStream({
  async start(controller) {
    const send = (d: object) => controller.enqueue(encoder.encode(sseEvent(d)));
    send({ type: "status", text: "Analyzing request..." });

    // State-based tool filtering (removing the means = reliable block)
    const activeTools = isBlocked
      ? allTools.filter((t) => t.name !== "call_report_formatter")
      : allTools;

    let loop = true;
    while (loop) {
      const res = await client.messages.create({ model, system, tools: activeTools, messages, max_tokens: 4096 });
      for (const b of res.content) if (b.type === "text" && b.text.trim()) send({ type: "orchestrator", text: b.text });
      if (res.stop_reason !== "tool_use") { loop = false; break; }

      messages.push({ role: "assistant", content: res.content });
      const toolResults = [];
      for (const b of res.content) {
        if (b.type !== "tool_use") continue;
        send({ type: "agent_start", agent: b.name, label, task });
        const result = await callSubAgent(/* ... */);   // execute the sub-agent
        send({ type: "agent_result", agent: b.name, label, result: result.text });
        toolResults.push({ type: "tool_result", tool_use_id: b.id, content: result.text });
      }
      messages.push({ role: "user", content: toolResults });
    }
    send({ type: "done", apiUsage: {} });
    controller.close();
  },
});
return new Response(stream, {
  headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", Connection: "keep-alive" },
});
```

**Recommended reusable event-type set**: `status` (info) / `orchestrator` (LLM plan text) / `agent_start` (sub-agent starts, carries `agent`/`label`/`task`) / `agent_result` (sub-agent result) / `done` (whole pipeline + usage totals) / `error`.

**Frontend consumption** — use `fetch` + `ReadableStream` (not `EventSource`, which can't carry a POST body):
```ts
const reader = res.body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  for (const line of decoder.decode(value).split("\n")) {
    if (!line.startsWith("data: ")) continue;
    const raw = line.slice(6).trim();
    if (!raw || raw === "[DONE]") continue;
    const ev = JSON.parse(raw);   // branch on ev.type
  }
}
```

**When to apply / Caveats**:
- Finish all early-blocking checks (cost cap / auth / quota) **before** opening the stream. Once the stream is open you can't change the HTTP status code, so gate with `new Response(..., { status })` first.
- Emit errors **inside** the stream via `send({ type: "error" })` then `controller.close()`. Throwing out of the stream leaves the client with a truncated response.
- SSE chunks can split at event boundaries. In production, buffer decoder output and parse on `\n\n` boundaries (line-only `\n` parsing is fragile under chunk splits).
- Put **side-effectful gating** (quota decrement, etc.) right before tool execution; on failure, put a failure marker in the `tool_result` so the LLM degrades gracefully.

---

## 2. Single-agent direct call + auto-continuation

**Problem**: An LLM response hits `max_tokens` and cuts off mid-way, leaving long output (reports) incomplete. You don't want the user to press a "continue" button.

**Approach**: On `stop_reason === "max_tokens"`, push the **accumulated assistant text + a continuation request (user)** onto the message history and re-call with the same model. Repeat up to N times, accumulating text. Sum token usage each call.

**Core snippet**:
```ts
let accumulated = "", contCount = 0, keepGoing = true;
const MAX_CONTINUATIONS = 3; // tune per tier/route
while (keepGoing) {
  const stream = client.messages.stream({ model, system, messages, max_tokens: 8192 });
  const res = await stream.finalMessage();
  accumulated += res.content.find((b) => b.type === "text")?.text ?? "";
  // accumulate usage (input/output/cacheRead/cacheCreation separately)

  if (res.stop_reason === "max_tokens" && contCount < MAX_CONTINUATIONS) {
    contCount++;
    messages.push(
      { role: "assistant", content: accumulated },
      { role: "user", content: "The previous response was cut off. Continue from exactly where it stopped. Do not repeat earlier content; resume naturally from the break point." },
    );
  } else keepGoing = false;
}
```

**When to apply / Caveats**:
- Keep the continuation prompt text in **one place**. If you have both a streaming route and an orchestrator sub-call using it, document "change one, change both" as a team rule.
- The continuation cap is a **cost-control lever**. Set it low (0–2) for free/low tiers, higher (5) for premium tiers — it determines worst-case cost.
- The assistant content you push must be the **full accumulation**, not just the latest delta, or the model loses context.
- In a streaming route the deltas are already on the wire, so continuation deltas stream naturally in sequence.

---

## 3. Machine-token-based i18n-safe parsing

**Problem**: Code must regex-parse specific values (an inferred category, a fit score, an input-validity flag) out of LLM output, but if the output language varies (ko/ja/en/...), **translated labels break the parser**. SpecForge originally parsed a Korean label and it broke in ja/en sessions when the LLM translated the label — the UI couldn't read the value.

**Approach**: Force the parse-target value to be emitted as a **language-invariant ASCII machine token**. Fix the colon/pipe/slash delimiters and the ASCII keywords regardless of response language; only the **value** (number, category name) is in the response language. State "do not translate these tokens" in the prompt's language directive.

**Core snippet** (token format — forced on the first line):
```
INFERRED_ROLE: {category} ({region})
FIT_SCORE: 72/100 | grade: B | must: 4/6 | want: 2/3
INPUT_INVALID: {reason}      # reason ∈ empty | not_relevant | irrelevant  (ASCII-fixed)
```
Parser (language-agnostic):
```ts
export function extractInferredRole(text: string): string {
  const m =
    text.match(/INFERRED_ROLE\s*[:：]\s*(.+)/) ||          // new format (ASCII token)
    text.match(/legacy-localized-label\s*[:：]\s*(.+)/);   // legacy fallback (old-session compat)
  return m ? m[1].trim() : "";
}
// score: /FIT_SCORE\s*:\s*(\d+)\s*\/\s*100/, grade: /grade\s*:\s*([SABCD])/i
```
Invariant declaration to embed in the prompt's language directive:
> "Keep these format tokens exactly as the given ASCII/digits (do not translate): INFERRED_ROLE / FIT_SCORE / INPUT_INVALID / [HOST] / [COACH] / section numbers `### 1`–`### 5`."

**When to apply / Caveats**:
- Keep tokens **line-scoped** and force them at a fixed position (first line). The UI detects the line, extracts the value, then hides the line from display.
- Use a validity token (e.g. `INPUT_INVALID`) as a **control signal** to trigger side-effects language-agnostically (UI block, server quota refund): `/^INPUT_INVALID:\s*(empty|not_relevant|irrelevant)/m`.
- When migrating from a localized label to an ASCII token, keep a **legacy label fallback** in the parser for old data / cache compatibility.
- Accept the full-width colon too (`[:：]`) to absorb CJK input.
- Conversely, never expose the token name (a code identifier) in **user-visible** body text — render table headers etc. in natural language ("Fit score").

---

## 4. Language + agent based model selection + per-model cost accounting

**Problem**: A cheap model underperforms in one specific language (e.g. Japanese kanji quality). Upgrading every request to an expensive model destroys margin. And mixing models makes **cost accounting inaccurate if a single flat rate is assumed**.

**Approach**:
- **Partially upgrade** by `(agent, language)` combination. Use the expensive model only for "core agents × quality-sensitive languages"; keep the cheap default otherwise. An explicit model in the request body wins.
- Branch cost accounting on the **actual model's pricing table** (`pricingForModel`), accumulating USD per call. This is what keeps the daily cost cap accurate.

**Core snippet**:
```ts
export function selectModelForAgent(agent: string, language?: string): ModelId {
  const isCoreAgent = agent === "analyst" || agent === "report_formatter";
  return (isCoreAgent && isJaOrEn(language)) ? PREMIUM_MODEL : DEFAULT_MODEL;
}
export function pricingForModel(model: string): ModelPricing {
  return model === PREMIUM_MODEL
    ? { input: 3, output: 15, cacheRead: 0.3, cacheCreation: 3.75 }  // expensive
    : { input: 1, output: 5, cacheRead: 0.1, cacheCreation: 1.25 };  // default
}
const model = requestedModel && isValidModel(requestedModel)
  ? requestedModel : selectModelForAgent(agent, language);
accumulatedCostUSD += usageToCostUSD(model, inTok, outTok, cacheCreateTok, cacheReadTok);
```

**When to apply / Caveats**:
- Keep the upgrade condition **narrow** (core agents + specific language) so the default path's cost/behavior stays completely unchanged. Not touching the baseline session is the core of margin defense.
- Keep continuation (auto-continuation) **on the same model** for consistent accounting and quality.
- Reflect cache read/creation tokens in pricing too — omitting them makes the cost cap underestimate real spend.
- Handle model IDs as constants (`AVAILABLE_MODELS`/`isValidModel`); never hardcode in routes, so a model swap is a one-line constant change.

---

## 5. Deterministic post-processing safety net

**Problem**: LLM output retains a repeatable, predictable class of error (e.g. Japanese kanji misspellings). Re-calling an LLM to fix it adds cost/latency, and prompt hardening never fully eliminates it.

**Approach**: A **zero-LLM-call** deterministic dictionary (substitution table) post-processes output just before return. To avoid over-correction, register only "certain errors" (few), and **preserve parser-critical formats** (machine-token lines, code blocks).

**Core snippet**:
```ts
const CORRECTIONS: ReadonlyArray<readonly [RegExp, string]> = [
  [/圧教/g, "圧迫"], [/采用/g, "採用"], /* ...only certain misspellings */
];
const MACHINE_TOKEN_LINE = /^\s*(INPUT_INVALID|INFERRED_ROLE|FIT_SCORE|GAP)\b/;

export function correctText(text: string): string {
  const lines = text.split("\n");
  let inCode = false;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trimStart().startsWith("```")) { inCode = !inCode; continue; }  // preserve code fences
    if (inCode) continue;
    if (MACHINE_TOKEN_LINE.test(lines[i])) continue;                              // preserve machine-token lines
    for (const [re, rep] of CORRECTIONS) lines[i] = lines[i].replace(re, rep);
  }
  return lines.join("\n");
}
```

**When to apply / Caveats**:
- **Conservative mapping**: never add an ambiguous substitution that could break a valid word — only combinations that are impossible in context.
- Lines with a format contract (machine tokens / code blocks / invariant headings) must be **whitelist-skipped**. Prevents post-processing from breaking the parser.
- In a streaming route the deltas are already sent, so only when text **actually changed** emit the corrected full text as a separate event (`{ corrected }`) for the client to swap in — avoids needless re-transmission.
- Compose the mapping only from that specific language's misspellings, so it's safe to apply across all languages/agents.

---

## 6. Prompt-parser contract (invariant headings)

**Problem**: The UI parses a structured LLM document (a multi-section report) by heading to split it into tabs/views. But the report is **generated in multiple languages**, so heading text gets translated and a text-matching parser breaks immediately.

**Approach**: Make the prompt and parser contract **on numbers (structure), not text**. Keep headings as `### N. {title}`, force the **number, `### `, and single-line format to be invariant** while allowing the title text to be translated. The parser splits on a **number-based regex**, not the title.

**Core snippet**:
```ts
// Parser: split on "### N." numbers, not title text → language-agnostic
function parseSections(md: string): Section[] | null {
  const parts = md.split(/(?=^#{2,3}\s+\d+\.)/m).filter((s) => s.trim());
  const out: Section[] = [];
  for (const p of parts) {
    const m = p.match(/^#{2,3}\s+(\d+)\.\s+(.+?)(?:\r?\n|$)/m);
    if (m) out.push({ number: parseInt(m[1]), title: m[2].trim(), content: p });
  }
  return out.length >= 2 ? out : null;   // fallback to plain render on parse failure
}
```
The prompt side **generates and injects** per-language heading sets but forbids changing the format (number / `### ` / single line):
```ts
// getSectionHeadings(language) → injects ko/ja/en heading label sets into the prompt
en: ["### 1. Overall Summary", /* ... */ "### 5. Before & After Comparison"]
```

**When to apply / Caveats**:
- **Document the two-way contract**: "prompt heading ↔ parser regex ↔ UI tab-label mapping" breaks if one side changes alone. SpecForge nails these 5 headings as "never change" across several team docs and puts it in the code-review checklist.
- Give the parser a **fallback**: if sections fall below a threshold (e.g. 2), abandon structured parsing and fall back to plain markdown — a format deviation never becomes a screen collapse.
- Absorb value extraction (grade, pass likelihood) with **multi-language fallback regex** (ko/ja/en labels + false-positive-preventing lookahead). Separate from the heading contract.
- Only parse on translation-safe keys (section numbers, machine tokens); never use natural language as a parse key — same philosophy as pattern 3.
