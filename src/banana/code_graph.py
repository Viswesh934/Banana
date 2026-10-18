"""Codebase AST & Dependency Graph Indexer for Banana.

Analyzes local codebases to construct an architectural knowledge graph:
- Files, Classes, Functions, and Interfaces
- Import hierarchies and module dependencies
- Call graphs and symbol relationships
- Architectural boundary and layer detection

Zero external dependencies (uses standard Python `ast`).
"""

import ast
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from banana.db import FalkorDBClient, get_db_client
from banana.models import PriorityClass
from banana.tokenizer import count_tokens


class CodebaseIndexer:
    """Extracts and indexes code structure into Banana's Knowledge Graph."""

    def __init__(self, db_client: Optional[FalkorDBClient] = None, root_dir: Optional[str] = None) -> None:
        self.db_client = db_client or get_db_client()
        self.root_dir = Path(root_dir or Path.cwd()).resolve()

    def index_repository(self, max_files: int = 200) -> Dict[str, Any]:
        """Scan and index all python source files into the knowledge graph."""
        k_graph = self.db_client.get_knowledge_graph()
        stats = {
            "files_indexed": 0,
            "classes_indexed": 0,
            "functions_indexed": 0,
            "imports_indexed": 0,
        }

        ignored_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".mypy_cache", ".pytest_cache", ".banana"}

        files_to_index: List[Path] = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".")]
            for f in files:
                if f.endswith(".py"):
                    files_to_index.append(Path(root) / f)
                    if len(files_to_index) >= max_files:
                        break
            if len(files_to_index) >= max_files:
                break

        for file_path in files_to_index:
            try:
                rel_path = file_path.relative_to(self.root_dir).as_posix()
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                parsed = self._parse_file(rel_path, content)

                # 1. Create File node
                k_graph.query(
                    """
                    MERGE (f:ContextNode {canonical_id: $id})
                    SET f.title = $title,
                        f.content = $content,
                        f.entity_type = 'File',
                        f.priority = $priority,
                        f.token_cost = $token_cost
                    RETURN f.canonical_id
                    """,
                    {
                        "id": f"file_{rel_path.replace('/', '_')}",
                        "title": rel_path,
                        "content": f"Source file: {rel_path} ({len(content.splitlines())} lines)",
                        "priority": int(PriorityClass.BACKGROUND),
                        "token_cost": 25,
                    },
                )
                stats["files_indexed"] += 1

                # 2. Create Class and Function nodes
                for cls_info in parsed["classes"]:
                    cls_id = f"cls_{rel_path.replace('/', '_')}_{cls_info['name']}"
                    k_graph.query(
                        """
                        MERGE (c:ContextNode {canonical_id: $id})
                        SET c.title = $title,
                            c.content = $content,
                            c.entity_type = 'Class',
                            c.priority = $priority,
                            c.token_cost = $token_cost
                        RETURN c.canonical_id
                        """,
                        {
                            "id": cls_id,
                            "title": f"class {cls_info['name']}",
                            "content": f"Class {cls_info['name']} in {rel_path}:\n{cls_info.get('docstring', '')}\nMethods: {', '.join(cls_info['methods'])}",
                            "priority": int(PriorityClass.TOOL_SCHEMA),
                            "token_cost": 60,
                        },
                    )
                    k_graph.query(
                        "MATCH (f:ContextNode {canonical_id: $fid}), (c:ContextNode {canonical_id: $cid}) "
                        "MERGE (f)-[r:DEFINES]->(c) RETURN type(r)",
                        {"fid": f"file_{rel_path.replace('/', '_')}", "cid": cls_id},
                    )
                    stats["classes_indexed"] += 1

                for fn_info in parsed["functions"]:
                    fn_id = f"fn_{rel_path.replace('/', '_')}_{fn_info['name']}"
                    sig = fn_info.get("signature", fn_info["name"])
                    k_graph.query(
                        """
                        MERGE (fn:ContextNode {canonical_id: $id})
                        SET fn.title = $title,
                            fn.content = $content,
                            fn.entity_type = 'Function',
                            fn.priority = $priority,
                            fn.token_cost = $token_cost
                        RETURN fn.canonical_id
                        """,
                        {
                            "id": fn_id,
                            "title": f"def {fn_info['name']}",
                            "content": f"Function {sig} in {rel_path}:\n{fn_info.get('docstring', '')}",
                            "priority": int(PriorityClass.EVIDENCE),
                            "token_cost": 50,
                        },
                    )
                    k_graph.query(
                        "MATCH (f:ContextNode {canonical_id: $fid}), (fn:ContextNode {canonical_id: $fnid}) "
                        "MERGE (f)-[r:DEFINES]->(fn) RETURN type(r)",
                        {"fid": f"file_{rel_path.replace('/', '_')}", "fnid": fn_id},
                    )
                    stats["functions_indexed"] += 1

                # 3. Create Import Edges
                for imp in parsed["imports"]:
                    imp_clean = imp.replace(".", "_")
                    cypher_imp = """
                    MATCH (src:ContextNode {canonical_id: $src})
                    MATCH (tgt:ContextNode {entity_type: 'File'})
                    WHERE tgt.canonical_id = $cand1 
                       OR tgt.canonical_id = $cand2
                       OR tgt.canonical_id ENDS WITH $cand3
                    MERGE (src)-[r:IMPORTS]->(tgt)
                    RETURN count(r)
                    """
                    try:
                        k_graph.query(
                            cypher_imp,
                            {
                                "src": f"file_{rel_path.replace('/', '_')}",
                                "cand1": f"file_{imp_clean}.py",
                                "cand2": f"file_src_{imp_clean}.py",
                                "cand3": f"_{imp_clean}.py",
                            },
                        )
                        stats["imports_indexed"] += 1
                    except Exception:
                        pass

            except Exception:
                continue

        return stats

    def get_codebase_summary(self) -> Dict[str, Any]:
        """Fetch high-level architectural metrics and component overview from the knowledge graph."""
        k_graph = self.db_client.get_knowledge_graph()
        counts_res = k_graph.query(
            "MATCH (n:ContextNode) RETURN n.entity_type, count(n)"
        )
        entity_counts = {r[0]: r[1] for r in counts_res.result_set if r[0]}

        edges_res = k_graph.query(
            "MATCH ()-[r]->() RETURN type(r), count(r)"
        )
        edge_counts = {r[0]: r[1] for r in edges_res.result_set if r[0]}

        # Fetch key files
        files_res = k_graph.query(
            "MATCH (f:ContextNode {entity_type: 'File'}) RETURN f.title, f.content ORDER BY f.title LIMIT 30"
        )
        files = [{"path": r[0], "summary": r[1]} for r in files_res.result_set]

        # Fetch key classes
        classes_res = k_graph.query(
            "MATCH (c:ContextNode {entity_type: 'Class'}) RETURN c.title, c.content ORDER BY c.title LIMIT 30"
        )
        classes = [{"name": r[0], "details": r[1]} for r in classes_res.result_set]

        return {
            "entity_counts": entity_counts,
            "edge_counts": edge_counts,
            "files": files,
            "classes": classes,
        }

    def assemble_code_context(self, query: str, token_budget: int = 1500) -> Dict[str, Any]:
        """Assembles high-signal code context (signatures, interfaces, dependencies) under budget."""
        k_graph = self.db_client.get_knowledge_graph()
        tokens_used = 0
        selected_nodes: List[Dict[str, Any]] = []

        # Find matching symbols
        cypher = """
        MATCH (n:ContextNode)
        WHERE (n.entity_type IN ['Class', 'Function', 'File'])
          AND (n.canonical_id CONTAINS $kw OR n.title CONTAINS $kw OR n.content CONTAINS $kw)
        RETURN n.canonical_id, n.title, n.content, n.entity_type, n.token_cost
        LIMIT 25
        """
        res = k_graph.query(cypher, {"kw": query.strip().lower()})

        for row in res.result_set:
            cid, title, content, etype, cost = row[0], row[1], row[2], row[3], row[4] or 50
            if tokens_used + cost <= token_budget:
                tokens_used += cost
                selected_nodes.append({
                    "id": cid,
                    "type": etype,
                    "title": title,
                    "snippet": content,
                })

        assembled_prompt = "\n\n".join([f"### [{node['type']}] {node['title']}\n{node['snippet']}" for node in selected_nodes])

        return {
            "query": query,
            "token_budget": token_budget,
            "tokens_used": tokens_used,
            "symbols_count": len(selected_nodes),
            "assembled_context": assembled_prompt,
        }

    def _parse_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        """Parse AST of a single file to extract imports, classes, and top-level functions."""
        result: Dict[str, Any] = {"imports": [], "classes": [], "functions": []}
        try:
            tree = ast.parse(content)
        except Exception:
            return result

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result["imports"].append(node.module)

        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef):
                methods = [m.name for m in stmt.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                doc = ast.get_docstring(stmt) or ""
                result["classes"].append({
                    "name": stmt.name,
                    "methods": methods[:8],
                    "docstring": doc[:200],
                })
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(stmt) or ""
                args = [a.arg for a in stmt.args.args]
                sig = f"{stmt.name}({', '.join(args[:6])})"
                result["functions"].append({
                    "name": stmt.name,
                    "signature": sig,
                    "docstring": doc[:200],
                })

        return result
