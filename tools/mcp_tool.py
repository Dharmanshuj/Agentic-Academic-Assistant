from langchain.tools import tool
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client
import asyncio
import os

# Configuration for MCP Server
MCP_SERVER_COMMAND = "python"
MCP_SERVER_ARGS = ["mcp/mcp_server.py"]

async def call_mcp_tool(name: str, args: dict):
    """Internal helper to connect and call an MCP tool."""
    async with stdio_client(MCP_SERVER_COMMAND, MCP_SERVER_ARGS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, args)
            return result.content[0].text if result.content else "No result returned."

@tool
def get_employee_details_mcp(employee_id: str):
    """Retrieve complete employee profile including personal and job details using employee ID via MCP."""
    return asyncio.run(call_mcp_tool("get_employee_details", {"employee_id": employee_id}))

@tool
def get_employee_attendance_mcp(employee_id: str, month: int, year: int):
    """Fetch attendance records for an employee for a specific month and year via MCP."""
    return asyncio.run(call_mcp_tool("get_employee_attendance", {"employee_id": employee_id, "month": month, "year": year}))

@tool
def get_employee_salary_mcp(employee_id: str, month: int, year: int):
    """Retrieve salary breakdown including earnings and deductions for an employee via MCP."""
    return asyncio.run(call_mcp_tool("get_employee_salary", {"employee_id": employee_id, "month": month, "year": year}))

@tool
def get_all_employees_data_mcp():
    """Retrieve complete data of all employees (ADMIN access required) via MCP."""
    return asyncio.run(call_mcp_tool("get_all_employees_data", {}))

@tool
def get_all_employees_salary_mcp(month: int, year: int):
    """Retrieve salary data for all employees for a given month and year via MCP."""
    return asyncio.run(call_mcp_tool("get_all_employees_salary", {"month": month, "year": year}))

@tool
def get_all_employees_attendance_mcp(month: int, year: int):
    """Retrieve attendance records for all employees for a given month and year via MCP."""
    return asyncio.run(call_mcp_tool("get_all_employees_attendance", {"month": month, "year": year}))
