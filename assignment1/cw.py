# CloudWatch
import datetime
import boto.ec2.cloudwatch
from .settings import EC2_DEFAULT_REGION


cw = boto.ec2.cloudwatch.connect_to_region(EC2_DEFAULT_REGION)


def get_cpu_stat(cw, instanced_id, minutes=10):
    """Get average CPU Utilization in percentage of the instance"""
    assert type(minutes) == int
    now = datetime.datetime.now()
    start_time = now - datetime.timedelta(minutes=minutes)
    end_time = now
    stat = cw.get_metric_statistics(
        perid=minutes * 60,
        start_time=start_time,
        end_time=end_time,
        metric_name='CPUUtilization',
        namespace='AWS/EC2',
        statistics='Average',
        dimensions={'InstanceId': [instanced_id]},
        unit='Percent'
        )

    return stat * 100
