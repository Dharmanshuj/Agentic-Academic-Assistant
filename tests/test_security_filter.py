from security.filter import filter_record

def run_test():

    record = {
        "name": "John",
        "department": "HR",
        "salary": 100000,
        "ssn":7865,
        "password":"hello123",
        "token":"asdf",
        "api_key":9878866
    }

    filtered = filter_record(record)

    print("Filtered:", filtered)

run_test()