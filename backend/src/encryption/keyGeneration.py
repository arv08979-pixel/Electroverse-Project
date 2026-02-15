import os
from Crypto.Random import get_random_bytes

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, "configs")
KEY_PATH = os.path.join(CONFIG_DIR, "secret.key")

def load_key():
    if not os.path.exists(KEY_PATH):
        os.makedirs(CONFIG_DIR, exist_ok=True)

        key = get_random_bytes(32)
        with open(KEY_PATH, "wb") as f:
            f.write(key)

        return key

    with open(KEY_PATH, "rb") as f:
        return f.read()
