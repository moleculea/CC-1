# For security concerns and better portability, the following variables
# are set in ~/.boto:
# `AWS_ACCESS_KEY_ID'
# `AWS_SECRET_ACCESS_KEY'
import os


PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
DB_PATH = os.path.abspath(os.path.join(PROJECT_PATH, os.pardir, "db"))
DB_FILES = {
    "addresses": os.path.join(DB_PATH, "addresses"),
    "snapshots": os.path.join(DB_PATH, "snapshots"),
}

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
EC2_DEFAULT_WAIT_INTERVAL = 5
EC2_DEFAULT_DATA_DEVICE = "/dev/sdf"

# Hour (24-hour) after which all instances will be labeled `idle'
EC2_INSTANCE_IDLE_TIME = 19

# CPU utilization (percent) where an instance will be labeled `idle'
EC2_INSTANCE_IDLE_CPU = 20

# Autoscale config
AS_DEFAULT_MIN_SIZE = 1
AS_DEFAULT_MAX_SIZE = 3
AS_DEFAULT_CPU_UP = "80"
AS_DEFAULT_CPU_DOWN = "20"
