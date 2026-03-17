from .policy import SENSITIVE_FIELDS


def validate_query(query: str):

    query_lower = query.lower()

    for field in SENSITIVE_FIELDS:

        if field in query_lower:
            raise Exception(
                f"Access to sensitive field '{field}' is not allowed."
            )

    return True