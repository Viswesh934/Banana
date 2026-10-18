# How a failed SaaS pricing calculator, a 3 AM Gemini quota meltdown, and FalkorDB led us to build Banana.

> **Disclaimer:** I genuinely wanted to ask GPT to write this entire blog, slam my laptop shut, and enjoy 14 uninterrupted hours of sleep. But at 4 AM, staring at graph queries and a dead Gemini quota, I figured the internet deserved to know what happened. Also, the best blog post wins Apple AirPods 5. I'm not above risking my dignity for noise cancellation. 🎧

---

## Why We Built Banana

Banana started as a B2B SaaS pricing calculator. After hours of wrestling with Streamlit and discount sliders, I asked myself:

*Would I ever voluntarily use this product?*

The answer was no.

Meanwhile, AI coding agents were making the same mistakes over and over: forgetting architectural decisions, breaking dependency boundaries, and consuming huge amounts of context just to understand a codebase.

So we nuked the UI and pivoted.

```bash
git rm -rf ui/ components/ deal_calculator.py
git commit -m "pivot: delete pricing sliders, embrace the void"
```

Meet **Banana**: a graph-powered memory and context engine for coding agents. It helps tools like Claude Code and Cursor retrieve code relationships, remember architectural decisions, and check explicit rules through MCP.

---

## 3 AM: Gemini Has Left the Chat

Our Gemini API quota ran out during testing.

Instead of feeding the model dozens of source files for every question, we'd already indexed our codebase into FalkorDB:

- 39 files
- 42 classes
- 84 functions
- 275 import and call relationships

That changed everything. Banana could query the graph directly to retrieve dependencies, inspect code structure, and recall stored decisions without spending LLM tokens on those operations.

The graph became our memory—and our fallback when the model wasn't available.

---

## Less Context. Better Answers. (Enter Edmonds-Karp)

Give an agent a 2,000-token budget. Which files should it read?

Keyword search can return irrelevant matches. Vector search can find similar text without capturing the dependency relationships that matter.

Banana treats context assembly as a **Maximum-Flow Network Problem**:
- Imagine your token window is a pipe network with a maximum capacity (e.g., 950 or 2,000 tokens).
- The file or function you're editing is the **Source**; your Token Budget is the **Sink**.
- Every AST dependency edge (imports, calls, inheritance) acts as a pipe with capacity weighted by PageRank and architectural relevance.

Using the **Edmonds-Karp algorithm** (BFS augmenting paths), Banana pushes maximum information flow from the target file to the token budget. Instead of slicing files in half or stuffing random snippets, Edmonds-Karp routes complete, unbroken interfaces and critical dependencies until the token pipe is full.

The goal: **give the agent what it needs, not everything you have.**

---

## Ephemeral Graphs: A Scratchpad That Won't Trash Production

When an agent wants to reason through speculative changes—like testing a hypothetical refactor, simulating a breaking dependency, or asking "what if I change this interface?"—you never want it writing directly to your persistent codebase graph.

Because FalkorDB is built on in-memory GraphBLAS linear algebra, creating and tearing down graphs takes milliseconds, not minutes.

Banana takes full advantage of this with **Ephemeral Scratchpad Graphs**:
- Whenever an agent enters speculative simulation mode, Banana spins up an isolated micro-graph (`banana_scratch_<session_id>`) in under **5 milliseconds**.
- The agent simulates AST diffs, tests scenario policies, and checks cyclic dependencies in complete isolation.
- Once the simulation concludes, the scratchpad is dropped with a single command. 

Zero disk clutter, zero persistent memory corruption, and zero risk of hallucinated agent thoughts polluting your source of truth.

---

## Guardrails Without an LLM Call

Suppose an agent tries to import a low-level database driver directly into a UI component.

If that dependency violates an explicit architectural rule, Banana can check the relevant graph relationships and flag the violation without asking an LLM to review it.

We also built deterministic checks for patterns such as hardcoded credentials and unsafe code primitives.

Our measured latency for the tested AST security and boundary check was **0.28 ms**.

Not every security problem can be caught with a simple rule, but explicit constraints shouldn't need an LLM call every time.

---

## The Architecture

![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/z0us3477246abwa5b8k0.png)

Banana connects coding agents to an MCP server that exposes tools for code indexing, context assembly, guardrails, and persistent memory.

Behind the scenes, FalkorDB manages three graph layers:

- `banana_knowledge` — code structure, dependencies, and architectural decisions.
- `banana_demand` — architectural rules, invariants, and constraints.
- `banana_scratch_*` — ephemeral micro-graphs for isolated reasoning and policy simulations.

We deployed the service on AWS Lambda in `ap-south-1`, backed by FalkorDB Cloud.

---

## What We Learned

1. **Code is a graph, not just text.** Imports, calls, and class relationships matter when retrieving context.
2. **Not every problem needs an LLM.** Deterministic checks can enforce explicit rules faster and more predictably.
3. **Memory matters only when it's retrieved.** Saving decisions is useful; bringing them back at the right time is what makes them valuable.
4. **Ephemeral graphs unlock safe agent speculation.** Giving agents an instant, disposable graph sandbox prevents real-world codebase pollution.

---

## The Final Summoning 🍌

Whenever the coding agent encounters another architectural disaster, circular import, or hallucinated token overflow...

**WITH THIS TREASURE, I SUMMON MAHORAGA!**

```text
               布瑠部由良由良 (FURUBE YURAYURA...)
               
               "Turn the Wheel of the GraphBLAS Matrices.
                Adapt to all circular dependencies.
                Shatter the invalid boundary imports.
                Absorb the token budget overflow.
                No architectural violation shall pierce this domain!"
```

*The wheel has spun. The graph adapts. The code survives. Now give me my AirPods.* 🎧

---

**Built with:** FalkorDB, AWS Lambda, Python, and an alarming quantity of espresso.

**GitHub:** https://github.com/Viswesh934/Banana

**Live endpoint:** https://ssrr3wg2ibyqkh6gph4ehlthay0ovdzp.lambda-url.ap-south-1.on.aws/

**Demo:** *[Insert demo video link]*
