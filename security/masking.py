from .policy import MASKED_FIELDS


def account_no_mask(account_no: str):

    return  "****" + account_no[-4:]

def mask_phone(phone: str):

    return phone[:2] + "******" + phone[-2:]



def apply_masking(record: dict):

    if "account_no" in record:
        record["account_no"] = account_no_mask(record["account_no"])

    if "phone" in record:
        record["phone"] = mask_phone(record["phone"])

    return record