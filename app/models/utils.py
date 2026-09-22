import secrets


def generate_unique_id():
    # '15' bytes results in exactly 20 URL-safe characters
    # It uses A-Z, a-z, 0-9, and symbols like "-" and "_"
    return secrets.token_urlsafe(15)