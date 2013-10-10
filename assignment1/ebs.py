# Elastic Block Store
from .settings import EC2_DEFAULT_EBS_AZ, EC2_DEFAULT_EBS_SIZE


def initialize_data_volume(conn):
    vol = conn.create_volume(size=EC2_DEFAULT_EBS_SIZE,
                             zone=EC2_DEFAULT_EBS_AZ)
    return vol

