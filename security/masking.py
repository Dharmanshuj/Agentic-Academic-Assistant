from .policy import MASKED_FIELDS


def mask_email(email: str):

    name, domain = email.split("@")

    return f"{name[0]}***@{domain}"


def mask_phone(phone: str):

    return phone[:2] + "******" + phone[-2:]


def apply_masking(record: dict):

    if "email" in record:
        record["email"] = mask_email(record["email"])

    if "phone" in record:
        record["phone"] = mask_phone(record["phone"])

    return record