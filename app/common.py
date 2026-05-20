import string
import random

def generate_key(length=16):
    return "".join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for i in range(0, length))