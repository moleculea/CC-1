import boto.ec2
from .settings import EC2_DEFAULT_REGION


conn = boto.ec2.connect_to_region(EC2_DEFAULT_REGION)
