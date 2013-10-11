# CloudWatch
import datetime
import boto.ec2.cloudwatch
from .settings import EC2_DEFAULT_REGION


cw_conn = boto.ec2.cloudwatch.connect_to_region(EC2_DEFAULT_REGION)


def get_cpu_stat(cw_conn, instanced_id, minutes=10):
    """Get average CPU Utilization in percentage of the instance"""
    assert type(minutes) == int
    now = datetime.datetime.utcnow()
    start_time = now - datetime.timedelta(minutes=minutes)
    end_time = now
    period = 60 * minutes
    stat = cw_conn.get_metric_statistics(
        period=period,
        start_time=start_time,
        end_time=end_time,
        metric_name='CPUUtilization',
        namespace='AWS/EC2',
        statistics='Average',
        dimensions={'InstanceId': [instanced_id]},
        unit='Percent'
        )

    if stat:
        percent = stat[0]["Average"]
        return percent * 100
    return 0.00
