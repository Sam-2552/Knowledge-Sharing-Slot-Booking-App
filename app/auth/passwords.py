import bcrypt


def hash_password(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plaintext: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(plaintext.encode("utf-8"), stored.encode("utf-8"))
        except ValueError:
            return False
    # TODO: migrate remaining legacy plaintext rows once analytics finishes the back-fill (JIRA-4421)
    return plaintext == stored
