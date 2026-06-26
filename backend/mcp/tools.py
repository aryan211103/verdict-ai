"""
IBM Context Forge MCP tool definitions — penalty shootout game.

Each tool maps 1-to-1 with a FastAPI endpoint.  The gateway reads
these schemas and exposes them to any MCP-compatible client (e.g. a
Granite agent) so it can create sessions and submit kicks programmatically.

NOTE: player/team names are cosmetic in every tool.  The AI keeper in
      vs_ai mode uses session history only — no external player data.
"""

TOOLS = [
    {
        "name": "create_shootout_session",
        "description": (
            "Create a new penalty shootout session between two teams. "
            "Team names and player lists are cosmetic display labels — "
            "they do not affect game probabilities or AI behaviour. "
            "Returns a session_id used in all subsequent calls."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["team_a", "team_b"],
            "properties": {
                "team_a": {
                    "type": "object",
                    "required": ["team_name", "players"],
                    "properties": {
                        "team_name": {"type": "string", "description": "Display name for Team A"},
                        "players":   {"type": "array", "items": {"type": "string"},
                                      "description": "Ordered list of player names (cosmetic)"},
                    },
                },
                "team_b": {
                    "type": "object",
                    "required": ["team_name", "players"],
                    "properties": {
                        "team_name": {"type": "string"},
                        "players":   {"type": "array", "items": {"type": "string"}},
                    },
                },
                "mode": {
                    "type": "string",
                    "enum": ["1v1", "vs_ai"],
                    "default": "1v1",
                    "description": (
                        "'1v1': two humans supply cell + dive each kick. "
                        "'vs_ai': human supplies cell; AI chooses dive using "
                        "in-session shot history only."
                    ),
                },
                "seed": {
                    "type": "integer",
                    "description": "Optional RNG seed for reproducible games (testing).",
                },
            },
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "mode":       {"type": "string"},
                "team_a":     {"type": "string"},
                "team_b":     {"type": "string"},
                "message":    {"type": "string"},
            },
        },
        "endpoint": "POST /game/session",
    },
    {
        "name": "submit_kick",
        "description": (
            "Submit one penalty kick in an active session. "
            "In 1v1 mode: provide both cell (shooter's choice) and dive (keeper's choice). "
            "In vs_ai mode: provide only cell; the AI keeper picks the dive automatically. "
            "Returns the kick outcome and updated session state."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["session_id", "cell", "dive"],
            "properties": {
                "session_id": {"type": "string"},
                "cell": {
                    "type": "string",
                    "enum": ["TL","TC","TR","ML","MC","MR","BL","BC","BR"],
                    "description": (
                        "Shooter's target cell on the 3×3 goal grid "
                        "(T=top, M=mid, B=bottom; L=left, C=centre, R=right — "
                        "from the shooter's perspective)."
                    ),
                },
                "dive": {
                    "type": "string",
                    "enum": ["L", "C", "R"],
                    "description": (
                        "Keeper's dive direction (from the shooter's perspective). "
                        "Ignored in vs_ai mode."
                    ),
                },
            },
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "outcome": {
                    "type": "object",
                    "properties": {
                        "kick_number": {"type": "integer"},
                        "phase":       {"type": "string"},
                        "team":        {"type": "string"},
                        "player":      {"type": "string", "description": "Cosmetic label only"},
                        "cell":        {"type": "string"},
                        "dive":        {"type": "string"},
                        "matched":     {"type": "boolean"},
                        "cell_type":   {"type": "string"},
                        "p_goal":      {"type": "number"},
                        "goal":        {"type": "boolean"},
                    },
                },
                "session":           {"type": "object"},
                "ai_session_counts": {"type": "object", "nullable": True},
            },
        },
        "endpoint": "POST /game/session/{session_id}/kick",
    },
    {
        "name": "get_session_state",
        "description": (
            "Return the current state of a shootout session without advancing it. "
            "Includes score, kicks taken, current team, phase, and (in vs_ai mode) "
            "the AI's shot-direction counts for this session."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["session_id"],
            "properties": {
                "session_id": {"type": "string"},
            },
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "session":           {"type": "object"},
                "ai_session_counts": {"type": "object", "nullable": True},
            },
        },
        "endpoint": "GET /game/session/{session_id}",
    },
    {
        "name": "delete_session",
        "description": "Remove a completed or abandoned shootout session.",
        "inputSchema": {
            "type": "object",
            "required": ["session_id"],
            "properties": {
                "session_id": {"type": "string"},
            },
        },
        "outputSchema": {"type": "null"},
        "endpoint": "DELETE /game/session/{session_id}",
    },
]
