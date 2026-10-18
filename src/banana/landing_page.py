"""Landing Page HTML generator for Banana AWS Lambda Function URL."""

def get_landing_page_html(lambda_url: str = "") -> str:
    """Returns an interactive, sleek dark-mode landing page for the Banana Lambda endpoint."""
    return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🍌 Banana — Autonomous Graph Brain for AI Coding Agents</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['"Plus Jakarta Sans"', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'monospace'],
          }},
          colors: {{
            banana: {{
              400: '#fde047',
              500: '#eab308',
              600: '#ca8a04',
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    body {{
      background: radial-gradient(circle at top, #1e1b4b 0%, #090d16 50%, #030712 100%);
      color: #f3f4f6;
    }}
    .glow {{
      box-shadow: 0 0 50px -10px rgba(234, 179, 8, 0.25);
    }}
    .glow-card {{
      box-shadow: 0 0 30px -15px rgba(56, 189, 248, 0.15);
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col font-sans selection:bg-banana-500 selection:text-black">

  <!-- Navbar -->
  <header class="border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md sticky top-0 z-50">
    <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-3xl">🍌</span>
        <div>
          <span class="font-extrabold text-xl tracking-tight text-white">Banana</span>
          <span class="text-xs ml-2 font-mono px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-400 border border-yellow-500/30">v0.1.0-live</span>
        </div>
      </div>
      <div class="flex items-center space-x-4 text-sm font-medium">
        <a href="#console" class="text-slate-300 hover:text-yellow-400 transition">Live Console</a>
        <a href="#quickstart" class="text-slate-300 hover:text-yellow-400 transition">Quickstart</a>
        <a href="https://github.com/Viswesh934/Banana" target="_blank" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold transition flex items-center space-x-2 border border-slate-700">
          <span>GitHub</span>
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd"/></svg>
        </a>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <main class="flex-grow max-w-6xl mx-auto px-6 py-16">
    <div class="text-center max-w-3xl mx-auto space-y-6">
      
      <!-- Live Cloud Badge -->
      <div class="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>AWS Lambda Serverless Engine Live in ap-south-1</span>
        <span class="text-slate-500">•</span>
        <span>Powered by FalkorDB Cloud (~2.5ms latency)</span>
      </div>

      <h1 class="text-5xl md:text-6xl font-extrabold tracking-tight text-white leading-tight">
        The Autonomous Graph Brain for <span class="text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-yellow-400 to-amber-500">AI Coding Agents</span>
      </h1>
      
      <p class="text-lg md:text-xl text-slate-300 leading-relaxed">
        Banana supercharges external coding assistants (<strong>Cursor</strong>, <strong>Claude Code</strong>, <strong>Windsurf</strong>) with <strong>photographic cross-session memory</strong>, <strong>AST symbol dependency graphs</strong>, and <strong>deterministic guardrails</strong> powered by FalkorDB's ultra-fast GraphBLAS sparse matrix engine.
      </p>

      <!-- Key Value Badges -->
      <div class="pt-2 flex flex-wrap justify-center gap-3 text-xs font-mono">
        <span class="px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300">⚡ $0 Server Token Cost</span>
        <span class="px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300">🧠 FalkorDB Dual-Graph</span>
        <span class="px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300">🔒 Zero-Token Policy Guardrails</span>
        <span class="px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300">🔌 Model Context Protocol (MCP)</span>
      </div>
    </div>

    <!-- Live Interactive Console -->
    <div id="console" class="mt-16 rounded-2xl border border-slate-800 bg-slate-900/80 p-8 glow-card">
      <div class="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <h2 class="text-2xl font-bold text-white flex items-center gap-2">
            <span>⚡</span> Live Serverless API Console
          </h2>
          <p class="text-sm text-slate-400">Execute real-time graph traversals and guardrails on this AWS Lambda endpoint.</p>
        </div>
        <div class="flex items-center space-x-2 text-xs font-mono bg-slate-950 px-3 py-2 rounded-lg border border-slate-800">
          <span class="text-emerald-400">Endpoint:</span>
          <span class="text-slate-300 truncate max-w-xs">{lambda_url or "https://ssrr3wg2ibyqkh6gph4ehlthay0ovdzp.lambda-url.ap-south-1.on.aws/"}</span>
        </div>
      </div>

      <!-- Test Action Buttons -->
      <div class="mt-6 flex flex-wrap gap-3">
        <button onclick="runTest('health', {{}})" class="px-4 py-2.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-sm font-semibold transition flex items-center space-x-2">
          <span>🟢</span>
          <span>1. Graph Health & Connection</span>
        </button>

        <button onclick="runTest('guardrails', {{source_file: 'src/ui/app.py', imported_module: 'banana.db'}})" class="px-4 py-2.5 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 text-sm font-semibold transition flex items-center space-x-2">
          <span>🧱</span>
          <span>2. Test Clean Architecture Boundary (UI importing DB)</span>
        </button>

        <button onclick="runTest('guardrails', {{code: 'AWS_ACCESS_KEY_ID = \'AKIAIOSFODNN7EXAMPLE\''}})" class="px-4 py-2.5 rounded-lg bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-500/40 text-sm font-semibold transition flex items-center space-x-2">
          <span>🔒</span>
          <span>3. Test Credential Leak Guardrail (OWASP)</span>
        </button>

        <button onclick="runTest('query_decisions', {{limit: 5}})" class="px-4 py-2.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 text-sm font-semibold transition flex items-center space-x-2">
          <span>🧠</span>
          <span>4. Query Team Architectural Memory</span>
        </button>

        <button onclick="runTest('query', {{query: 'MATCH (n:ContextNode) RETURN n.entity_type, count(n) AS node_count'}})" class="px-4 py-2.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 text-sm font-semibold transition flex items-center space-x-2">
          <span>🔍</span>
          <span>5. Query Codebase Graph Nodes</span>
        </button>
      </div>

      <!-- Output Display Box -->
      <div class="mt-6 relative">
        <div class="flex items-center justify-between bg-slate-950 px-4 py-2 rounded-t-lg border-t border-x border-slate-800 text-xs font-mono text-slate-400">
          <div class="flex items-center space-x-2">
            <span class="w-3 h-3 rounded-full bg-red-500/60 inline-block"></span>
            <span class="w-3 h-3 rounded-full bg-yellow-500/60 inline-block"></span>
            <span class="w-3 h-3 rounded-full bg-green-500/60 inline-block"></span>
            <span class="ml-2 font-bold text-slate-300" id="action-label">Ready • Click a test above</span>
          </div>
          <span id="latency-label" class="text-emerald-400"></span>
        <pre id="output-box" class="bg-slate-950 border border-slate-800 rounded-b-lg p-5 font-mono text-sm text-yellow-300 overflow-x-auto min-h-[160px] max-h-[360px]">&#123;
  "status": "ready",
  "message": "Click any button above to execute a real-time request against AWS Lambda and FalkorDB Cloud."
&#125;</pre>
    </div>

    <!-- 3 Core Superpowers -->
    <div class="mt-20">
      <h2 class="text-3xl font-extrabold text-white text-center">Why Coding Agents Need Banana</h2>
      <p class="text-center text-slate-400 mt-2">Solving the three fatal flaws of Cursor, Claude Code, and Windsurf.</p>
      
      <div class="grid md:grid-cols-3 gap-8 mt-10">
        <!-- Card 1 -->
        <div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-4 hover:border-yellow-500/40 transition">
          <div class="w-12 h-12 rounded-lg bg-yellow-500/10 border border-yellow-500/30 flex items-center justify-center text-2xl">
            🧠
          </div>
          <h3 class="text-xl font-bold text-white">Photographic Memory</h3>
          <p class="text-sm text-slate-300 leading-relaxed">
            Eliminates session amnesia. When architectural decisions are made, Banana commits them to FalkorDB with a <code class="text-yellow-400 font-mono text-xs">:SUPERSEDES</code> lineage graph so tomorrow's session respects past decisions.
          </p>
        </div>

        <!-- Card 2 -->
        <div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-4 hover:border-yellow-500/40 transition">
          <div class="w-12 h-12 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-2xl">
            ⚡
          </div>
          <h3 class="text-xl font-bold text-white">AST Graph Knapsack</h3>
          <p class="text-sm text-slate-300 leading-relaxed">
            Eliminates prompt bloat. Banana indexes your codebase into AST symbols (<code class="text-cyan-400 font-mono text-xs">:File</code>, <code class="text-cyan-400 font-mono text-xs">:Class</code>, <code class="text-cyan-400 font-mono text-xs">:Function</code>) and assembles high-signal interfaces under strict token budgets using Edmonds-Karp max-flow.
          </p>
        </div>

        <!-- Card 3 -->
        <div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-4 hover:border-yellow-500/40 transition">
          <div class="w-12 h-12 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center text-2xl">
            🛑
          </div>
          <h3 class="text-xl font-bold text-white">Deterministic Guardrails</h3>
          <p class="text-sm text-slate-300 leading-relaxed">
            Sub-millisecond rule validation enforcing Clean Architecture boundaries (UI cannot import DB drivers directly) and preventing credential leaks (OWASP API key and private key detection) before code is committed—burning 0 LLM tokens.
          </p>
        </div>
      </div>
    </div>

    <!-- Quickstart / MCP Connection -->
    <div id="quickstart" class="mt-20 rounded-2xl border border-slate-800 bg-slate-900/60 p-8">
      <h2 class="text-2xl font-bold text-white flex items-center gap-2">
        <span>🔌</span> Connect Banana to Your Coding Agent
      </h2>
      <p class="text-slate-400 text-sm mt-1">Plug into Claude Code or Cursor in 10 seconds via Model Context Protocol (MCP).</p>

      <div class="grid md:grid-cols-2 gap-6 mt-6">
        <!-- Claude Code -->
        <div class="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
          <div class="flex items-center justify-between">
            <span class="font-bold text-white text-sm">1. Claude Code CLI</span>
            <span class="text-xs font-mono text-slate-500">Terminal Command</span>
          </div>
          <pre class="bg-slate-900 p-3 rounded-lg text-xs font-mono text-yellow-300 overflow-x-auto">claude mcp add banana -- uv run banana mcp --url {lambda_url or "https://ssrr3wg2ibyqkh6gph4ehlthay0ovdzp.lambda-url.ap-south-1.on.aws/"}</pre>
        </div>

        <!-- Cursor IDE -->
        <div class="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-3">
          <div class="flex items-center justify-between">
            <span class="font-bold text-white text-sm">2. Cursor IDE</span>
            <span class="text-xs font-mono text-slate-500">.cursor/mcp.json</span>
          </div>
          <pre class="bg-slate-900 p-3 rounded-lg text-xs font-mono text-yellow-300 overflow-x-auto">{{
  "mcpServers": {{
    "banana": {{
      "command": "uv",
      "args": ["run", "banana", "mcp", "--url", "{lambda_url or 'https://ssrr3wg2ibyqkh6gph4ehlthay0ovdzp.lambda-url.ap-south-1.on.aws/'}"]
    }}
  }}
}}</pre>
        </div>
      </div>
    </div>

  </main>

  <!-- Footer -->
  <footer class="border-t border-slate-800/80 bg-slate-950/80 py-8 text-center text-sm text-slate-500">
    <p>🍌 Banana Coding Agent • Built with FalkorDB & AWS Lambda • Zero Server AI Token Cost</p>
  </footer>

  <!-- Interactive Test Script -->
  <script>
    async function runTest(action, params) {{
      const label = document.getElementById('action-label');
      const latencyLabel = document.getElementById('latency-label');
      const box = document.getElementById('output-box');

      label.innerText = 'Calling action: ' + action + '...';
      latencyLabel.innerText = 'Executing...';
      box.innerText = 'Sending request to AWS Lambda...';

      const startTime = performance.now();
      try {{
        const response = await fetch(window.location.href, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ action: action, params: params }})
        }});
        const data = await response.json();
        const duration = Math.round(performance.now() - startTime);

        label.innerText = 'Action: ' + action + ' • Status ' + response.status;
        latencyLabel.innerText = 'Roundtrip: ' + duration + 'ms (Lambda latency: ' + (data.latency_ms || 'N/A') + 'ms)';
        box.innerText = JSON.stringify(data, null, 2);
      }} catch (err) {{
        label.innerText = 'Error calling Lambda';
        latencyLabel.innerText = '';
        box.innerText = JSON.stringify({{ error: err.message }}, null, 2);
      }}
    }}
  </script>
</body>
</html>"""
