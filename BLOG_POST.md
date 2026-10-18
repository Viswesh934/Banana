# How I Tried to Build a SaaS Pricing Calculator, Burned My Gemini Quota at 3 AM, and Accidentally Built a Graph-Powered Coding Brain

> *Disclaimer: I genuinely wanted to just ChatGPT this entire blog post, close my laptop, and go live my life for 14 uninterrupted hours. But at 4:00 AM, staring at a terminal glowing with sub-3ms GraphBLAS query times and an empty Gemini quota, something in my caffeine-drenched soul whispered: "No. The internet deserves to know what actually happened." Also, the best blog post wins Apple AirPods 5, and I am not above putting my pride on the line for noise cancellation.*

---

## Act 1: The Day 1 Delusion — "Let's Build Deal Intelligence!"

Every hackathon starts with pure, unadulterated hubris.

On morning one, our project wasn't called an "Autonomous Graph-Aware Coding Agent." It was called **Banana Deal Desk**—a B2B SaaS pricing and margin discount calculator. The vision was so corporate it practically wore a fleece vest: sales reps would drag sliders, the app would calculate EBITDA margin compression, and it would spit out approval workflows.

I spent the first four hours wrestling with Streamlit and CSS flexboxes. Sliders for discount percentages. Multipliers for multi-year contracts. Color-coded badges for "Healthy Margin" vs. "CFO Will Fire You." 

It looked like an enterprise dashboard from 2017 had a bad fever dream.

Around hour six, the existential dread hit. I leaned back, looked at the UI, and asked myself the most dangerous question you can ask during a hackathon: 

> *"Would I ever, in a million years, voluntarily use this product?"*

The answer was a resounding, hollow **no**. 

Meanwhile, every developer in 2026—including me—was wrestling with a much more painful, daily reality: **AI coding agents are brilliant amnesiacs.** 

You ask Cursor, Copilot, or Claude to refactor a service, and it cheerfully writes code that:
1. Violates your Clean Architecture boundaries (importing low-level database drivers into your UI layer).
2. Forgets decisions you made two hours ago in another branch.
3. Chokes on your 20,000-token codebase and burns your API credits down to the subatomic level.

So right then and there, we made the call: **Nuke the UI.** 

```bash
git rm -rf ui/ components/ deal_calculator.py
git commit -m "pivot: delete pricing sliders, embrace the void"
```

No more sliders. No more discount margins. We were going to build what modern agents actually need: **an MCP Server and a Graph-Orchestrated Brain for coding agents**, backed by an AST knowledge graph.

---

## Act 2: The Skeptic's Guide to FalkorDB — "Is This Just Redis with a Mustache?"

When someone first suggested FalkorDB for our codebase knowledge graph, my immediate reaction was peak developer skepticism:

> *"Wait... isn't FalkorDB just RedisGraph with a rebrand? Or worse, Neo4j that takes 4GB of RAM just to clear its throat?"*

I expected a clunky wrapper around key-value pairs that falls apart the moment you ask for a 3-hop traversal. 

I was dead wrong.

FalkorDB isn't a Redis knockoff. Under the hood, it’s powered by **GraphBLAS**—which means it represents graph nodes and relationships as **sparse linear algebra matrices** written in optimized C. 

When you ask a traditional graph database:
```cypher
MATCH (f:File {path: 'src/banana/agent.py'})-[:IMPORTS*1..3]->(dep:File)
RETURN dep.path
```
Most engines do slow, recursive pointer-chasing in memory. FalkorDB? **It performs sparse matrix multiplication.**

Here’s what our production metrics on FalkorDB Cloud looked like:
- **3-Hop Multi-Edge Dependency Traversal**: `17.4 ms`
- **Architectural Decision Memory Retrieval**: `1.37 ms`
- **AST Security & Boundary Check**: `0.28 ms`

It wasn't just fast; it was answering queries faster than Python’s `json.dumps()` could serialize the dictionary. For an AI agent operating in tight feedback loops, sub-millisecond graph lookups are the difference between an agent that feels snappy and one that feels like it’s thinking in slow motion.

---

## Act 3: When the Gemini Quota Died (The 3 AM Panic)

Everything was humming along. We hooked up our agent to Google’s Gemini API, set up prompt chains, and started testing codebase queries.

And then, at 2:48 AM, the screen turned red:

```text
google.api_core.exceptions.ResourceExhausted: 429 Quota Exceeded / 503 UNAVAILABLE
```

My free-tier Gemini credits had vaporized. 

When you build a standard "RAG" coding agent, you stuff dozens of raw source files into the prompt and pray the LLM pays attention. That burns 40,000 to 80,000 tokens per prompt. In less than an hour of automated testing, our quota was deader than disco.

In a normal project, this is where you pack up your backpack, submit a broken slide deck, and go to bed. But because we had already mapped our entire repository’s Abstract Syntax Tree (AST) into FalkorDB:

- **39 Files**
- **42 Classes**
- **84 Functions**
- **275 IMPORTS and CALLS Edges**

We realized something profound: **An agent doesn't need to ask an LLM about code structure when the graph already knows the absolute truth.**

When our Gemini connection threw a 503 error, our agent didn’t crash. It simply queried the FalkorDB AST graph directly, resolving dependencies, class hierarchies, and architectural paths in pure Cypher. Zero tokens spent. Zero API calls wasted. 

The graph became both the brain and the shock absorber.

---

## Act 4: Edmonds-Karp & The 0-Token Guardrail (In Plain English)

To make Banana work as a production-grade MCP server, we solved two foundational problems that plague LLMs:

### 1. The Context Knapsack (Edmonds-Karp Max-Flow)
LLM context windows are expensive. If you give an agent a 2,000-token budget, which files should it read?
- Lexical search (grep) grabs irrelevant keyword matches.
- Vector search (RAG) grabs semantically similar paragraphs that lack functional context.

We modeled context selection as a **Max-Flow Network Problem**. Imagine your token budget is a pipe that can only push 2,000 units of water. Every source file, function, and import relationship has a "capacity" based on its PageRank and dependency proximity to the active file.

Using the **Edmonds-Karp algorithm** on our FalkorDB graph, Banana computes the maximum flow of architectural relevance from the target file (Source) to the Token Budget (Sink). It packs the exact, highest-signal 950 tokens into the prompt with zero bloat.

### 2. The Zero-Token Guardrail
Suppose a developer (or a hallucinating LLM) writes this code:
```python
# In src/ui/views/dashboard.py
from src.database.engine import get_raw_db_connection
```
Most modern setups would send this code to GPT-4 with a 500-token prompt: *"Please review this code for Clean Architecture violations."* That costs money and takes 2 seconds.

Banana queries the FalkorDB schema:
```cypher
MATCH (caller:File {path: 'src/ui/views/dashboard.py'}), (callee:File {path: 'src/database/engine.py'})
MATCH path = (caller)-[:IMPORTS]->(callee)
WHERE caller.layer = 'presentation' AND callee.layer = 'infrastructure'
RETURN path
```
FalkorDB detects the boundary violation in **0.28 milliseconds**. **0 LLM tokens. 0 API dollars.** It rejects the pull request before the compiler even wakes up.

---

## Act 5: The Architecture (From Zero to Live Cloud Deployment)

Here is the final architecture we deployed:

```text
┌────────────────────────────────────────────────────────┐
│             Developer Tools & IDEs                     │
│  (Claude Desktop / Cursor / VS Code / banana CLI)      │
└───────────────────────────┬────────────────────────────┘
                            │ Standard MCP (JSON-RPC)
                            ▼
┌────────────────────────────────────────────────────────┐
│             AWS Lambda MCP Server                      │
│        (Python 3.12 Serverless Gateway)                │
│                                                        │
│   • banana_health_check         • banana_guardrails    │
│   • banana_orchestrate_context  • banana_query_memory  │
└───────────────────────────┬────────────────────────────┘
                            │ Encrypted TLS / Sub-3ms Cypher
                            ▼
┌────────────────────────────────────────────────────────┐
│             FalkorDB Cloud (ap-south-1)                │
│             GraphBLAS Matrix Engine                    │
│                                                        │
│   (File) ──[:IMPORTS]──► (File) ──[:DEFINES]──►(Class) │
│     │                      │                           │
│     └─────[:ADR_LINK]─────► (DecisionRecord)           │
└────────────────────────────────────────────────────────┘
```

- **Live MCP Lambda URL**: [https://ssrr3wg2ibyqkh6gph4ehlthay0ovdzp.lambda-url.ap-south-1.on.aws/](https://ssrr3wg2ibyqkh6gph4ehlthay0ovdzp.lambda-url.ap-south-1.on.aws/)
- **GitHub Repository**: [https://github.com/Viswesh934/Banana](https://github.com/Viswesh934/Banana)
- **Demo Video**: `[DEMO VIDEO LINK HERE]`

---

## Act 6: What We Learned (And What's Next for FalkorDB)

1. **Graphs beat vectors for code**: Code is not a collection of unstructured blog posts. Code is a strict, directed mathematical graph of calls, inheritance, and imports. Storing code in vectors is like navigating a city using only smell. Storing it in FalkorDB is having a GPS satellite.
2. **Deterministic guardrails save your wallet**: Let the LLM generate syntax, but let the Graph enforce the rules.
3. **What I’d love to see in FalkorDB next**:
   - Built-in probabilistic data structures like **HyperLogLog** and **Count-Min Sketch** directly accessible via Cypher (for cardinality estimation across massive codebases).
   - Better native hybrid search combining GraphBLAS matrix operations with dense vector indices without overhead.

---

## Epilogue: The Adaptation

At the end of this hackathon, looking at our live Lambda deployment intercepting architectural violations, assembling optimal token knapsacks, and persisting architectural memories across branches, only one thing felt appropriate to close this journey.

Whenever our coding agent encounters invalid imports, circular dependencies, or LLM hallucinations...

```text
               ╔═════════════════════════════════════════════════╗
               ║                                                 ║
               ║               With this treasure,               ║
               ║                   I SUMMON...                   ║
               ║                                                 ║
               ║           EIGHT-HANDLED SWORD DIVERGENT         ║
               ║          SILA DIVINE GENERAL MAHORAGA!          ║
               ║                                                 ║
               ╚═════════════════════════════════════════════════╝
```

```text
               布瑠部由良由良 (FURUBE YURAYURA...)
               
               "Turn the Wheel of the GraphBLAS Matrices.
                Adapt to all circular dependencies.
                Shatter the invalid boundary imports.
                Absorb the token budget overflow.
                No architectural violation shall pierce this domain!"
```

The wheel has spun. The graph has adapted. Now give me my AirPods. 🎧🍌

---
*Built with FalkorDB, AWS Lambda, Python 3.12, and an alarming quantity of espresso.*
