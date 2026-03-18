from tools.database_tool import query_employee_department

def run_test():

    department = "HR"

    result = query_employee_department.invoke({
        "department": department
    })

    print("Final AI-safe result:")
    print(result)

run_test()