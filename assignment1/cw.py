# CloudWatch
import boto.ec2.cloudwatch
from .settings import EC2_DEFAULT_REGION


cw = boto.ec2.cloudwatch.connect_to_region(EC2_DEFAULT_REGION)

