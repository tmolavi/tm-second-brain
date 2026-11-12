"""Model-independent stdio MCP server for TM Second Brain."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from ..core.models import ConfidenceLevel, MemoryScope, SearchQuery
from ..memory.markdown_store import MarkdownMemoryStore

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "memory_search",
        "description": "Search non-private vault memories with project isolation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "project": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "memory_recall",
        "description": "Recall active non-private memories scoped to a project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "memory_expand",
        "description": "Expand a memory's wikilink neighborhood.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string"},
                "depth": {"type": "integer", "default": 1},
            },
            "required": ["memory_id"],
        },
    },
    {
        "name": "memory_remember",
        "description": "Store a durable memory with provenance and conflict detection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "scope": {"type": "string", "enum": ["general", "platform", "project"]},
                "projects": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "string", "enum": ["verified", "inferred", "unverified"]},
                "verification": {"type": "string"},
                "source_agent": {"type": "string"},
            },
            "required": ["title", "body"],
        },
    },
    {
        "name": "memory_correct",
        "description": "Supersede an existing memory without overwriting history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string"},
                "new_title": {"type": "string"},
                "new_body": {"type": "string"},
                "reason": {"type": "string"},
                "source_agent": {"type": "string"},
            },
            "required": ["target_id", "new_title", "new_body", "reason"],
        },
    },
    {
        "name": "memory_health",
        "description": "Return vault and retrieval diagnostics.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


class MCPServer:
    """JSON-RPC 2.0 MCP server enforcing privacy and redaction on all responses."""

    def __init__(self, store: MarkdownMemoryStore) -> None:
        self.store = store

    def _safe_record_dict(self, rec_dict: dict[str, Any]) -> dict[str, Any]:
        rec_dict["body"] = self.store.privacy.redact(rec_dict["body"])
        return rec_dict

    def call_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatch an MCP tool call with strict privacy enforcement."""
        if name == "memory_search":
            hits = self.store.search(
                SearchQuery(
                    text=str(args["query"]),
                    project=args.get("project"),
                    include_private=False,
                    limit=int(args.get("limit", 10)),
                )
            )
            return {
                "results": [
                    {
                        "score": h.score,
                        "backend": h.backend,
                        "record": self._safe_record_dict(h.record.to_dict()),
                    }
                    for h in hits
                ]
            }

        if name == "memory_recall":
            recs = self.store.recall(
                project=args.get("project"),
                include_private=False,
                limit=int(args.get("limit", 20)),
            )
            return {"records": [self._safe_record_dict(r.to_dict()) for r in recs]}

        if name == "memory_expand":
            exp = self.store.expand(
                str(args["memory_id"]),
                depth=int(args.get("depth", 1)),
                include_private=False,
            )
            root = self._safe_record_dict(exp["root"].to_dict()) if exp["root"] else None
            neighbors = [self._safe_record_dict(n.to_dict()) for n in exp["neighbors"]]
            return {"root": root, "neighbors": neighbors}

        if name == "memory_remember":
            res = self.store.remember(
                str(args["title"]),
                str(args["body"]),
                scope=MemoryScope(args.get("scope", "project")),
                projects=args.get("projects"),
                confidence=ConfidenceLevel(args.get("confidence", "unverified")),
                verification=args.get("verification"),
                source_agent=str(args.get("source_agent", "mcp")),
                origin="mcp",
                private=False,
            )
            return {
                "record": self._safe_record_dict(res.record.to_dict()),
                "conflicts": [c.__dict__ for c in res.conflicts],
                "warnings": res.warnings,
            }

        if name == "memory_correct":
            res = self.store.correct(
                str(args["target_id"]),
                str(args["new_title"]),
                str(args["new_body"]),
                reason=str(args["reason"]),
                source_agent=str(args.get("source_agent", "mcp")),
            )
            return {"record": self._safe_record_dict(res.record.to_dict())}

        if name == "memory_health":
            return self.store.health()

        raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a single JSON-RPC 2.0 request."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}

        try:
            if method == "initialize":
                result: Any = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "tm-second-brain", "version": "0.1.0"},
                }
            elif method == "tools/list":
                result = {"tools": MCP_TOOLS}
            elif method == "tools/call":
                tool_name = str(params["name"])
                tool_args = params.get("arguments") or {}
                payload = self.call_tool(tool_name, tool_args)
                result = {
                    "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(exc)},
            }

    def serve_stdio(self, stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> None:
        """Run line-delimited JSON-RPC loop over stdio."""
        for line in stdin:
            raw = line.strip()
            if not raw:
                continue
            resp = self.handle_request(json.loads(raw))
            stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            stdout.flush()
