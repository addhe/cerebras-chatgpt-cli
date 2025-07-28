"""Token usage analytics tool for Cerebras CLI."""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .base import Tool, ToolParameter, ToolResult
from cerebras_cli.core.client import ResponseProcessor


class TokenAnalyticsTool(Tool):
    """Tool for tracking and analyzing token usage."""
    
    @property
    def name(self) -> str:
        return "token_analytics"
    
    @property
    def description(self) -> str:
        return "Track and analyze token usage across sessions"
    
    @property
    def category(self) -> str:
        return "analytics"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="operation",
            type=str,
            description="Operation: 'track', 'report', 'reset', 'export', 'import'",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="time_range",
            type=str,
            description="Time range for report: 'day', 'week', 'month', 'all'",
            required=False,
            default="all"
        ))
        self.add_parameter(ToolParameter(
            name="format",
            type=str,
            description="Output format: 'text', 'json', 'csv'",
            required=False,
            default="text"
        ))
        self.add_parameter(ToolParameter(
            name="file",
            type=str,
            description="File path for export/import operations",
            required=False
        ))
    
    async def execute(self, operation: str, time_range: str = "all", 
                     format: str = "text", file: Optional[str] = None) -> ToolResult:
        """Execute token analytics operations."""
        try:
            analytics_dir = Path.home() / ".cerebras-cli" / "analytics"
            analytics_dir.mkdir(parents=True, exist_ok=True)
            
            usage_file = analytics_dir / "token_usage.json"
            
            if operation == "track":
                # Track token usage from last response
                if not hasattr(self.context, "last_response"):
                    return ToolResult(
                        success=False,
                        error="No recent API response to track"
                    )
                
                usage_info = ResponseProcessor.extract_usage_info(self.context.last_response)
                if not usage_info:
                    return ToolResult(
                        success=False,
                        error="No token usage information found in last response"
                    )
                
                # Add timestamp
                usage_info["timestamp"] = datetime.now().isoformat()
                
                # Load existing data
                if usage_file.exists():
                    with open(usage_file, "r") as f:
                        data = json.load(f)
                else:
                    data = []
                
                # Add new entry and save
                data.append(usage_info)
                with open(usage_file, "w") as f:
                    json.dump(data, f, indent=2)
                
                return ToolResult(
                    success=True,
                    content=f"Tracked token usage: {usage_info['total_tokens']} tokens",
                    data=usage_info
                )
            
            elif operation == "report":
                if not usage_file.exists():
                    return ToolResult(
                        success=False,
                        error="No token usage data found"
                    )
                
                with open(usage_file, "r") as f:
                    data = json.load(f)
                
                # Filter by time range
                now = datetime.now()
                filtered_data = []
                
                for entry in data:
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if time_range == "day" and (now - entry_time) > timedelta(days=1):
                        continue
                    if time_range == "week" and (now - entry_time) > timedelta(days=7):
                        continue
                    if time_range == "month" and (now - entry_time) > timedelta(days=30):
                        continue
                    filtered_data.append(entry)
                
                # Generate report
                total_tokens = sum(entry["total_tokens"] for entry in filtered_data)
                avg_tokens = total_tokens / len(filtered_data) if filtered_data else 0
                
                if format == "json":
                    report = {
                        "time_range": time_range,
                        "total_tokens": total_tokens,
                        "average_tokens": avg_tokens,
                        "entry_count": len(filtered_data),
                        "entries": filtered_data
                    }
                    return ToolResult(
                        success=True,
                        content=json.dumps(report, indent=2),
                        data=report
                    )
                else:
                    report_text = f"Token Usage Report ({time_range}):\n"
                    report_text += f"Total tokens: {total_tokens}\n"
                    report_text += f"Average tokens per request: {avg_tokens:.1f}\n"
                    report_text += f"Number of requests: {len(filtered_data)}\n"
                    
                    if filtered_data:
                        report_text += "\nRecent Usage:\n"
                        for entry in filtered_data[-5:]:  # Show last 5 entries
                            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M")
                            report_text += f"{timestamp}: {entry['total_tokens']} tokens\n"
                    
                    return ToolResult(
                        success=True,
                        content=report_text,
                        data={
                            "total_tokens": total_tokens,
                            "average_tokens": avg_tokens,
                            "entry_count": len(filtered_data)
                        }
                    )
            
            elif operation == "reset":
                if usage_file.exists():
                    usage_file.unlink()
                
                return ToolResult(
                    success=True,
                    content="Token usage data reset successfully"
                )
            
            elif operation == "export":
                if not file:
                    return ToolResult(
                        success=False,
                        error="File path required for export operation"
                    )
                
                if not usage_file.exists():
                    return ToolResult(
                        success=False,
                        error="No token usage data to export"
                    )
                
                target_file = Path(file).expanduser().resolve()
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(usage_file, "r") as src, open(target_file, "w") as dst:
                    dst.write(src.read())
                
                return ToolResult(
                    success=True,
                    content=f"Token usage data exported to {file}"
                )
            
            elif operation == "import":
                if not file:
                    return ToolResult(
                        success=False,
                        error="File path required for import operation"
                    )
                
                source_file = Path(file).expanduser().resolve()
                if not source_file.exists():
                    return ToolResult(
                        success=False,
                        error=f"Source file not found: {file}"
                    )
                
                with open(source_file, "r") as src, open(usage_file, "w") as dst:
                    dst.write(src.read())
                
                return ToolResult(
                    success=True,
                    content=f"Token usage data imported from {file}"
                )
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation}. Use 'track', 'report', 'reset', 'export', or 'import'"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Token analytics operation failed: {e}"
            )
