from .policy import MASKED_FIELDS


def mask_email(email: str):

    name, domain = email.split("@")

    return f"{name[0]}***@{domain}"


def mask_phone(phone: str):

    return phone[:2] + "******" + phone[-2:]

def mask_account_no(account_no:str):

    return "********" + account_no[-4:]


def apply_masking(record: dict):

    if "email" in record:
        record["email"] = mask_email(record["email"])

    if "phone" in record:
        record["phone"] = mask_phone(record["phone"])
    
    if "account_no" in record:
        record["account_no"]=mask_account_no(record["account_no"])

    return record