from .policy import MASKED_FIELDS


def account_no_mask(account_no: str):

    return  "****" + account_no[-4:]

def mask_phone(phone: str):

    return phone[:2] + "******" + phone[-2:]

def mask_account_no(account_no:str):

    return "********" + account_no[-4:]



def apply_masking(record: dict):

    if "account_no" in record:
        record["account_no"] = account_no_mask(record["account_no"])

    if "phone" in record:
        record["phone"] = mask_phone(record["phone"])
    
    if "account_no" in record:
        record["account_no"]=mask_account_no(record["account_no"])

    return record