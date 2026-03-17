from security.masking import apply_masking

def run_test():

    record = {
        "name": "John",
        "email": "john@company.com"
    }

    masked = apply_masking(record)

    print(masked)

run_test()