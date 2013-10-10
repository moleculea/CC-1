import os
from .settings import EC2_DEFAULT_KEY_NAME, EC2_DEFAULT_KEY_PATH
from .utils import output


def initialize_key_pair(conn, name=EC2_DEFAULT_KEY_NAME):
    """Initialize key pair and download private key to default path"""
    key_pair = conn.create_key_pair(name)
    save_private_key(key_pair)
    return key_pair


def save_private_key(key_pair):
    path = os.path.join(EC2_DEFAULT_KEY_PATH, key_pair.name)
    msg = "Saving private key for '%s' to %s..." % (key_pair.name, path)
    output.debug(msg)
    key_pair.save(EC2_DEFAULT_KEY_PATH)


def get_key_pair(conn, name=EC2_DEFAULT_KEY_NAME):
    key_pair = conn.get_key_pair(name)
    if key_pair:
        return key_pair
    key_pair = initialize_key_pair(conn)
    return key_pair
