import re

def is_valid_email(email):
    if not isinstance(email, str):
        return False
    pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    return bool(re.match(pattern, email))

def is_positive_number(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False