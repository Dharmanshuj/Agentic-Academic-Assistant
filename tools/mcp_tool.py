"""
MCP Tool wrappers for the AI Agent.

Connects to the Spring Boot MCP server (via Streamable HTTP) and calls tools.
Each call runs in a dedicated daemon thread to avoid blocking application shutdown.
"""
import json
import asyncio
import concurrent.futures
import os
from typing import Optional

from langchain.tools import tool
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession
from langchain_core.runnables.config import RunnableConfig


# ── Spring Boot MCP Server URL ───────────────────────────────────────────────
SPRING_MCP_URL = os.getenv("SPRING_MCP_URL", "http://localhost:8080/mcp")
MCP_OPERATION_TIMEOUT_SECONDS = int(os.getenv("MCP_OPERATION_TIMEOUT_SECONDS", "20"))
MCP_THREAD_TIMEOUT_SECONDS = int(os.getenv("MCP_THREAD_TIMEOUT_SECONDS", "25"))

# Thread pool with daemon=True to allow the process to exit even if threads are hanging
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Hack to make ThreadPoolExecutor threads daemon-like for easier shutdown
# (ThreadPoolExecutor threads are not daemon by default and will block sys.exit)
def _daemon_executor_submit(fn, *args, **kwargs):
    def wrapper():
        return fn(*args, **kwargs)
    return _executor.submit(wrapper)


async def _call_mcp_tool(name: str, args: dict) -> str:
    """Connect to Spring Boot MCP server, call a tool, return the text result."""
    try:
        async with asyncio.timeout(MCP_OPERATION_TIMEOUT_SECONDS):
            async with streamable_http_client(SPRING_MCP_URL) as (read, write, _get_session_id):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(name, args)
                    if result.content:
                        return result.content[0].text
                    return json.dumps({"error": "No result returned."})
    except asyncio.TimeoutError:
        return json.dumps({"error": f"MCP tool call timed out ({MCP_OPERATION_TIMEOUT_SECONDS}s). Is Spring Boot running?"})
    except Exception as e:
        return json.dumps({"error": f"MCP tool call failed: {str(e)}"})


def _run_in_thread(name: str, args: dict) -> str:
    """Run the async MCP call in a fresh event loop on a separate thread."""
    return asyncio.run(_call_mcp_tool(name, args))


def _run(name: str, args: dict) -> dict:
    """Call an MCP tool from any context (sync or async). Returns parsed JSON."""
    future = _executor.submit(_run_in_thread, name, args)
    try:
        raw = future.result(timeout=MCP_THREAD_TIMEOUT_SECONDS)
    except concurrent.futures.TimeoutError:
        return {"error": "Technical Timeout: The MCP thread took too long to respond."}
    except Exception as e:
        return {"error": f"Technical Error: {str(e)}"}
        
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw}


# ── Student Tools ────────────────────────────────────────────────────────────

@tool
def get_student_by_id(config: RunnableConfig):
    """Query your student profile and return sanitized JSON record. Do not pass any arguments."""
    emp_id = config.get("configurable", {}).get("emp_id")
    if not emp_id:
        return json.dumps({"error": "Student ID not found in context."})
    return _run("get_student_by_id", {"studentId": emp_id})


@tool
def get_attendance(config: RunnableConfig, month: Optional[int] = None, year: Optional[int] = None):
    """Get your attendance for a specific month or year."""
    emp_id = config.get("configurable", {}).get("emp_id")
    if not emp_id:
        return json.dumps({"error": "Student ID not found in context."})
    args = {"studentId": emp_id, "month": month or 0, "year": year or 0}
    return _run("get_attendance", args)


@tool
def get_semester_results(semester: int):
    """Fetch results/grades for a specific semester."""
    return _run("get_semester_results", {"semester": semester})


@tool
def get_all_attendance_for_student(config: RunnableConfig, year: Optional[int] = None):
    """Get all your attendance records across all months for a specific year."""
    emp_id = config.get("configurable", {}).get("emp_id")
    if not emp_id:
        return json.dumps({"error": "Student ID not found in context."})
    args = {"studentId": emp_id, "year": year or 0}
    return _run("get_all_attendance_for_student", args)


# ── Admin Tools ──────────────────────────────────────────────────────────────

@tool
def get_all_students_data():
    """Query basic details for all students. ONLY allowed for ADMIN user."""
    return _run("get_all_students_data", {})

@tool
def get_all_students_academic_information():
    """Admin tool to get comprehensive academic information for all students. ONLY allowed for ADMIN user."""
    return _run("get_all_students_academic_information", {})

@tool
def admin_get_semester_metrics(semester: Optional[int] = None, year: Optional[int] = None):
    """Admin tool to get attendance and academic metrics for all students in a given semester. ONLY allowed for ADMIN user."""
    args = {"semester": semester or 0, "year": year or 0}
    return _run("admin_get_semester_metrics", args)
