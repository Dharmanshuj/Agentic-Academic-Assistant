from .policy import MASKED_FIELDS


def mask_email(email: str):
    parts = email.split("@")
    if len(parts) == 2:
        name = parts[0]
        return name[:2] + "****@" + parts[1]
    return "****"

def mask_phone(phone: str):
    return phone[:2] + "******" + phone[-2:]


def apply_masking(record: dict):

    if "email" in record:
        record["email"] = mask_email(record["email"])

    if "phone" in record:
        record["phone"] = mask_phone(record["phone"])

    return record