# Virtual machine operations
# 
from .conn import conn
from .settings import (EC2_DEFAULT_INSTANCE_TYPE, EC2_DEFAULT_IMAGE_ID,
                       EC2_DEFAULT_INSTANCE_NUM, EC2_DEFAULT_TAG_NAMES,
                       EC2_DEFAULT_WAIT_INTERVAL, EC2_DEFAULT_DATA_DEVICE)
from .sg import get_security_group
from .ebs import initialize_data_volume


def initialize_instances(conn):
    """Create instances from public AMIs provided by AWS"""
    sg = get_security_group(conn)
    kp = get_key_pair(conn)
    reservation = conn.run_instances(image_id=EC2_DEFAULT_INSTANCE_TYPE,
                       min_count=EC2_INSTANCE_NUM, max_count=EC2_INSTANCE_NUM,
                       security_groups=[sg.name],
                       key_name=kp.name,
                       instance_type=EC2_DEFAULT_INSTANCE_TYPE
                       monitoring_enabled=True)

    for instance in reservation.instances:
        while instance.update() == "pending":
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)

        if instance.update() == "running":
            vol = initialize_data_volume(conn)
            if vol.status == "available":
                vol.attach(instance.id, EC2_DEFAULT_DATA_DEVICE)

    instances = get_instances(conn, True)
    assign_tags(conn, instances, EC2_DEFAULT_TAG_NAMES)


def get_instances(conn, assert_num=False):
    """Get all instances associated with this account"""
    instances = conn.get_only_instances()
    if assert_num:
        # Confirm number of instances
        assert len(instances) == EC2_INSTANCE_NUM
    return instances


def list_instances_info(conn):
    instances = get_instances(conn)
    print _format_line("Name", "Instance ID", "State")
    print '-' * 45
    for instance in instances:
        name = instance.tags.get("Name", "-")
        instance_id = instance.id
        state = instance.state
        print _format_line(name, instance_id, state)


def _format_line(name, instance_id, state):
    fmt = "{name:{align}{width}}"
    fmt += " {instance_id:{align}{width}}"
    fmt += " {state:{align}{width}}"
    line = fmt.format(name=name, instance_id=instance_id, state=state,
                      align="<", width=15)
    return line


def assign_tags(conn, instances, tags):
    assert len(instances) == len(tags)
    for i, instance in enumerate(instances):
        conn.create_tags([instance.id], tags[i])


def main():
    instances = get_instances(conn)

    if len(instances):
        instances = get_instances(conn, True)

    # If no instance, initialize for the first time
    else:
        instances = initialize_instances(conn)
        list_instances_info(conn)









