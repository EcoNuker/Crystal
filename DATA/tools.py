import string, secrets


def gen_cryptographically_secure_string(size: int):
    """
    Generates a cryptographically secure string.
    """
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    f = "".join(secrets.choice(letters) for i in range(size))
    return f
