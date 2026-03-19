# Orchestrator Litmus Test

**A new orchestrator is required if and only if you need to change the shape of the execution loop.**

The execution loop is the core cycle: receive message → call LLM → process tools → repeat. If your requirement changes *when*, *how often*, or *what* drives that loop, you need a new orchestrator. If your requirement can be satisfied by reacting to events within the existing loop, compose on top of an existing one.

---

## When a New Orchestrator IS Needed

Use the **Create** path when your requirement changes the fundamental shape of the loop.

| # | Signal | What changes |
|---|--------|-------------|
| 1 | **WHEN the LLM is called** | The trigger condition for making an LLM call changes (e.g., on a timer, only when a condition is met, after a tool result is validated) |
| 2 | **HOW MANY TIMES the LLM is called** | The loop runs more than once by design (e.g., retry until convergence, N-turn debate, iterative refinement) |
| 3 | **WHICH PROVIDERS drive the loop** | Different LLM providers are called in the same loop (e.g., GPT-4 for drafting, Claude for critique — routing across providers is a loop-level concern) |
| 4 | **WHAT HAPPENS TO RESULTS** structurally | Results are aggregated, merged, ranked, or transformed in ways that require loop-level coordination (e.g., fan-out → synthesize, collect all tool results before continuing) |
| 5 | Tool dispatch changes from **sequential to parallel** | The orchestrator must fire multiple tools concurrently and await all results before the next LLM call |
| 6 | A **structured phase** is added before/after the main loop | A distinct phase with its own logic gate executes before the main loop starts or after it ends (e.g., plan phase → execute phase, validate phase → report phase) |

---

## When to Compose on Existing Orchestrators

Use the **Compose** path when you can achieve the requirement by reacting to events or configuring existing behavior.

| # | Mechanism | Use when |
|---|-----------|---------|
| 7 | **inject_context hook** | You need to inject feedback, validation results, or extra instructions into the LLM's context before it responds — the loop shape does not change |
| 8 | **deny / ask_user hook** | You need to block a tool call or permit it only after human approval — use `deny` to reject or `ask_user` to pause and wait for input |
| 9 | **observation hook** | You need passive logging, metrics, or side-effects triggered by loop events — the observation hook fires and returns without affecting the loop |
| 10 | **tool-task** for delegation | You need to delegate a sub-problem to another agent — tool-task handles this inside the existing loop without restructuring it |
| 11 | Internal tool async for parallelism within capability | You need parallel execution scoped to a single tool call — the tool itself issues concurrent requests; the orchestrator loop remains sequential |
| 12 | **orchestrator config** for provider selection | You need a different model or provider — configure the existing orchestrator rather than creating a new one |

---

## Applied Examples

Six concrete cases mapped to the Create/Compose decision:

| Scenario | Decision | Litmus Points | Pattern |
|----------|----------|---------------|---------|
| Run parallel web searches across 5 sources simultaneously | **Compose** | #11 | Internal tool async — the tool issues concurrent fetch calls; loop stays sequential |
| Route three LLMs to debate and synthesize their outputs | **Create** | #3, #4 | `loop-multi-provider` — WHICH PROVIDERS and WHAT HAPPENS TO RESULTS both change |
| Require approval before any dangerous tool executes | **Compose** | #8 | `ask_user` / `deny` hook — the loop shape does not change; only tool dispatch is gated |
| Add a planning step before execution begins | **Create** | #6 | `loop-phased` — a structured phase with its own logic precedes the main loop |
| Run until output quality converges (score ≥ threshold) | **Create** | #2 | `loop-convergence` — HOW MANY TIMES the LLM is called is determined dynamically |
| Fan out to 5 specialized agents and synthesize results | **Create** | #4, #6 | `loop-swarm` — WHAT HAPPENS TO RESULTS (merge) and a structured synthesis phase both require loop-level control |

---

## Decision Protocol

Follow these four steps in order to decide whether to Create or Compose:

1. **State the requirement precisely.** Write one sentence describing what the orchestrator must do differently from the default loop. Vague requirements produce wrong decisions.

2. **Apply the litmus test.** Check whether the requirement maps to points #1–#6 (Create) or #7–#12 (Compose). If it maps to a Compose mechanism, stop — do not create a new orchestrator.

3. **Check the catalog.** If the Create path is confirmed, look up `context/orchestrator/catalog.md` to find an existing orchestrator or pattern library entry that already implements the required loop shape. Prefer extending an existing pattern over building from scratch.

4. **Consult the kernel contracts.** Before writing any new orchestrator, read `context/orchestrator/kernel-contracts.md` to understand the `mount()` contract, the kernel event system, and the `HookResult` types your orchestrator may return. A new orchestrator that violates the kernel contract will fail protocol compliance validation.
