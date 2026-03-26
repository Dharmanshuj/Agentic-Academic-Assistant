from mcp.server import Server
import httpx

BASE_URL="http://localhost:8080"
server = Server("spring-mcp-adapter")
@server.tool(
    name="get_employee_details",
    description="Retrieve complete employee profile including personal and job details using employee ID",
    input_schema={
        "type": "object",
        "properties": {
            "employee_id": {
                "type": "string",
                "description": "Employee ID"
            }
        },
        "required": ["employee_id"]
    }
)
async def get_employee_details(employee_id: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/employees/{employee_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Backend error: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@server.tool(
    name="get_employee_attendance",
    description="Fetch attendance records for an employee for a specific month and year",
    input_schema={
        "type": "object",
        "properties": {
            "employee_id": {
                "type": "string",
                "description": "Employee ID"
            },
            "month": {
                "type": "integer",
                "description": "Month"
            },
            "year": {
                "type": "integer",
                "description": "Year"
            }
        },
        "required": ["employee_id", "month", "year"]
    }
)
async def get_employee_attendance(employee_id: str, month: int, year: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/employees/{employee_id}/attendance", params={"month": month, "year": year})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Backend error: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@server.tool(
    name="get_employee_salary",
    description="Retrieve salary breakdown including earnings and deductions for an employee for a specific month and year",
    input_schema={
        "type": "object",
        "properties": {
            "employee_id": {
                "type": "string",
                "description": "Employee ID"
            },
            "month": {
                "type": "integer",
                "description": "Month"
            },
            "year": {
                "type": "integer",
                "description": "Year"
            }
        },
        "required": ["employee_id", "month", "year"]
    }
)
async def get_employee_salary(employee_id: str, month: int, year: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/employees/{employee_id}/salary", params={"month": month, "year": year})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Backend error: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@server.tool(
    name="get_all_employees_data",
    description="Retrieve complete data of all employees (ADMIN access required)",
    input_schema={
        "type": "object",
        "properties": {
            "employee_id": {
                "type": "string",
                "description": "Employee ID"
            }
        }
    }
)
async def get_all_employees_data():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/employees")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Backend error: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@server.tool(
    name="get_all_employees_salary",
    description="Retrieve salary data for all employees for a given month and year (ADMIN access required)",
    input_schema={
        "type": "object",
        "properties": {
            "month": {
                "type": "integer",
                "description": "Month"
            },
            "year": {
                "type": "integer",
                "description": "Year"
            }
        },
        "required": ["month", "year"]
    }
)
async def get_all_employees_salary(month: int, year: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/employees/salary", params={"month": month, "year": year})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Backend error: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@server.tool(
    name="get_all_employees_attendance",
    description="Retrieve attendance records for all employees for a given month and year (ADMIN access required)",
    input_schema={
        "type": "object",
        "properties": {
            "month": {
                "type": "integer",
                "description": "Month"
            },
            "year": {
                "type": "integer",
                "description": "Year"
            }
        },
        "required": ["month", "year"]
    }
)
async def get_all_employees_attendance(month: int, year: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/employees/attendance", params={"month": month, "year": year})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Backend error: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    server.run(transport="stdio")