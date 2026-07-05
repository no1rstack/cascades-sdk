"""Cascades MCP Server — Model Context Protocol for AI assistants."""

from .server import main, TOOLS, handle_tool_call

__all__ = ["main", "TOOLS", "handle_tool_call"]
