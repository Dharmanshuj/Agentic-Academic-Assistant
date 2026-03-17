from tools.database_tool import query_employee_department

def run_test():

    result = query_employee_department.invoke(
        {"department": "HR"}
    )

    print(result)

run_test()