# For security concerns and better portability, the following variables 
# are set in ~/.boto:
# `AWS_ACCESS_KEY_ID'
# `AWS_SECRET_ACCESS_KEY'


EC2_DEFAULT_REGION = "us-east-1"
EC2_DEFAULT_EBS_AZ = "us-east-1b"
EC2_DEFAULT_EBS_SIZE = 2
EC2_DEFAULT_INSTANCE_TYPE = "t1.micro"
EC2_DEFAULT_IMAGE_ID = "ami-76f0061f"
EC2_DEFAULT_INSTANCE_NUM = 2
EC2_DEFAULT_TAG_NAMES = ["VM1", "VM2"]
EC2_DEFAULT_SG_NAME = "assignment1"
EC2_DEFAULT_SG_DESC = "security group for assignment1"
EC2_DEFAULT_SG_TCP_PORTS = [22, 80]
EC2_DEFAULT_KEY_NAME = "assignment1"
EC2_DEFAULT_KEY_PATH = "~"
EC2_DEFAULT_WAIT_INTERVAL = 10
EC2_DEFAULT_DATA_DEVICE = "/dev/sdh"