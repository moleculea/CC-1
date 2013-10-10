# Security groups
from .settings import (EC2_DEFAULT_SG_TCP_PORTS, EC2_DEFAULT_SG_NAME,
                       EC2_DEFAULT_SG_DESC)
from .utils import output


def initialize_security_group(conn):
    """Create a security group"""
    output.debug("Initializing security group...")
    sg = conn.create_security_group(EC2_DEFAULT_SG_NAME, EC2_DEFAULT_SG_DESC)
    for port in EC2_DEFAULT_SG_TCP_PORTS:
        sg.authorize('tcp', port, port, '0.0.0.0/0')
    return sg


def get_security_group(conn, name=EC2_DEFAULT_SG_NAME):
    sgs = conn.get_all_security_groups()
    for sg in sgs:
        if name == sg.name:
            return sg
    # If not found, initialize a new security group
    return initialize_security_group(conn)
