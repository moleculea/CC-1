import time
import boto.ec2
from boto.ec2.autoscale import (AutoScalingGroup,
                                LaunchConfiguration, ScalingPolicy)
from boto.ec2.cloudwatch import MetricAlarm
from boto.exception import BotoServerError
from .cw import cw_conn
from .keys import get_key_pair
from .settings import (EC2_DEFAULT_REGION, AS_DEFAULT_MIN_SIZE,
                       AS_DEFAULT_MAX_SIZE, EC2_DEFAULT_EBS_AZ,
                       AS_DEFAULT_CPU_UP, AS_DEFAULT_CPU_DOWN,
                       EC2_DEFAULT_INSTANCE_TYPE, EC2_DEFAULT_WAIT_INTERVAL)
from .sg import get_security_group
from .utils import output


as_conn = boto.ec2.autoscale.connect_to_region(EC2_DEFAULT_REGION)


def create_launch_configuration(conn, name, image_id):

    sg = get_security_group(conn)
    key_pair = get_key_pair(conn)

    lc = LaunchConfiguration(name=name, image_id=image_id,
                             key_name=key_pair.name, security_groups=[sg],
                             instance_type=EC2_DEFAULT_INSTANCE_TYPE,
                             instance_monitoring=True)

    as_conn.create_launch_configuration(lc)
    return lc


def create_auto_scaling_group(name, lc):
    ag = AutoScalingGroup(group_name=name,
                          availability_zones=[EC2_DEFAULT_EBS_AZ],
                          launch_config=lc, min_size=AS_DEFAULT_MIN_SIZE,
                          max_size=AS_DEFAULT_MAX_SIZE,
                          connection=as_conn)
    as_conn.create_auto_scaling_group(ag)
    return ag


def create_scaling_policies(as_name):
    """Create scaling up and scaling down policy"""

    scale_up_policy = ScalingPolicy(
        name='scale_up', adjustment_type='ChangeInCapacity',
        as_name=as_name, scaling_adjustment=1, cooldown=180)

    scale_down_policy = ScalingPolicy(
        name='scale_down', adjustment_type='ChangeInCapacity',
        as_name=as_name, scaling_adjustment=-1, cooldown=180)

    as_conn.create_scaling_policy(scale_up_policy)
    as_conn.create_scaling_policy(scale_down_policy)


def create_scaling_alarms(cw_conn, as_name):
    """Create scaling up and scaling down alarms using CloudWatch"""

    scale_up_policy = as_conn.get_all_policies(
        as_group=as_name, policy_names=['scale_up'])[0]

    scale_down_policy = as_conn.get_all_policies(
        as_group=as_name, policy_names=['scale_down'])[0]

    alarm_dimensions = {"AutoScalingGroupName": as_name}

    scale_up_alarm = MetricAlarm(
        name='scale_up_on_cpu', namespace='AWS/EC2',
        metric='CPUUtilization', statistic='Average',
        comparison='>', threshold=AS_DEFAULT_CPU_UP,
        period='60', evaluation_periods=2,
        alarm_actions=[scale_up_policy.policy_arn],
        dimensions=alarm_dimensions)

    scale_down_alarm = MetricAlarm(
        name='scale_down_on_cpu', namespace='AWS/EC2',
        metric='CPUUtilization', statistic='Average',
        comparison='<', threshold=AS_DEFAULT_CPU_DOWN,
        period='60', evaluation_periods=2,
        alarm_actions=[scale_down_policy.policy_arn],
        dimensions=alarm_dimensions)

    cw_conn.create_alarm(scale_up_alarm)
    cw_conn.create_alarm(scale_down_alarm)


def setup_autoscale_group(conn, name, image_id):
    """Set up autoscale for an instance"""
    msg = "Setting up Autoscale for instance %s (image_id: %s)..." \
        % (name, image_id)
    output.debug(msg)
    lc = get_launch_configuration(conn, name, image_id)
    groups = as_conn.get_all_groups(names=[name])
    if groups:
        name = groups[0].name
        fmsg = ("Autoscale group %s already/still exists. "
                "Please try again later, or make sure this group is deleted.")
        msg = fmsg % name
        output.warning()
    create_auto_scaling_group(name, lc)
    #as_conn.get_all_policies(policy_names=["scale_up", "scale_down"])
    create_scaling_policies(name)
    create_scaling_alarms(cw_conn, name)
    output.success("Autoscale group %s created." % name)


def delete_autoscale_group(conn, name):
    msg = "Deleting Autoscale group %s..." % name
    output.debug(msg)
    ag = as_conn.get_all_groups(names=[name])[0]
    ag.shutdown_instances()
    instance_ids = [i.instance_id for i in ag.instances]
    instances = conn.get_only_instances(instance_ids)
    msg = "Shutting down instances in this group..."
    output.debug(msg)
    activities = as_conn.get_all_activities(ag)
    time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
    for instance in instances:
        while instance.update() == "shutting-down":
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
    time.sleep(EC2_DEFAULT_WAIT_INTERVAL)

    try:
        ag.delete()
    except BotoServerError:
        output.warning("This group still has activities. Try again later.")

    output.success("Autoscale group %s deleted." % name)


def get_launch_configuration(conn, name, image_id):
    """Get or create launch configuration with specified name"""
    lcs = as_conn.get_all_launch_configurations(names=[name])
    for lc in lcs:
        if lc.name == name:
            return lc
    return create_launch_configuration(conn, name, image_id)

