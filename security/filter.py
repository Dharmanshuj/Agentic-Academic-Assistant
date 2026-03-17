from .policy import ALLOWED_COLUMNS

def filter_record(record: dict) -> dict:
    """
    Removes any column not allowed for AI access.
    """

    filtered = {}

    for key, value in record.items():

        if key in ALLOWED_COLUMNS:
            filtered[key] = value

    return filtered


def filter_records(records):

    return [filter_record(r) for r in records]