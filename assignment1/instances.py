# Virtual machine operations
import datetime
import time


from .addr import assign_addresses, get_addresses, release_all_addresses
from .autoscale import setup_autoscale_group, as_conn, delete_autoscale_group
from .conn import conn
from .cw import cw_conn, get_cpu_stat
from .ebs import (initialize_data_volume, get_snapshots, delete_all_snapshots,
                  delete_all_data_volumes, get_data_volumes)
from .keys import get_key_pair
from .settings import (EC2_DEFAULT_INSTANCE_TYPE, EC2_DEFAULT_IMAGE_ID,
                       EC2_DEFAULT_INSTANCE_NUM, EC2_DEFAULT_TAG_NAMES,
                       EC2_DEFAULT_WAIT_INTERVAL, EC2_DEFAULT_DATA_DEVICE,
                       EC2_DEFAULT_REGION, DB_FILES, EC2_DEFAULT_EBS_AZ)
from .sg import get_security_group
from .utils import output
import db
import pdb


def initialize_instances(conn):
    """
    Initialize instances (one-time operation)
    * Create and launch instances from public AMIs provided by AWS
    """
    # Empty local DB files
    db.write_data(DB_FILES["addresses"], [])
    db.write_data(DB_FILES["snapshots"], [])

    # Create or get (if any) security groups and key pairs
    sg = get_security_group(conn)
    key_pair = get_key_pair(conn)

    # Release all elastic IPs if any
    release_all_addresses(conn)

    output.debug("Launching instances for the first time...")
    reservation = conn.run_instances(
        image_id=EC2_DEFAULT_IMAGE_ID,
        min_count=EC2_DEFAULT_INSTANCE_NUM, max_count=EC2_DEFAULT_INSTANCE_NUM,
        security_groups=[sg.name],
        key_name=key_pair.name,
        instance_type=EC2_DEFAULT_INSTANCE_TYPE,
        placement=EC2_DEFAULT_EBS_AZ,
        monitoring_enabled=True
        )

    for i, instance in enumerate(reservation.instances):
        while instance.update() == "pending":
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)

        if instance.update() == "running":
            output.debug("Initializing EBS data volume for instance %d..." % i)
            volume = initialize_data_volume(conn)

            while volume.update() != "available":
                time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
            output.debug("Attaching EBS data volume for instance %d..." % i)
            volume.attach(instance.id, EC2_DEFAULT_DATA_DEVICE)

    instances = get_instances(conn, True, "running")
    msg = "Assigning tag names and public IPs for the running instances..."
    output.debug(msg)
    assign_tags(conn, instances, EC2_DEFAULT_TAG_NAMES)
    assign_addresses(conn, instances)
    output.success("All instances are initialized.")


def store_instances(conn, copy_snapshots=False, idle_only=False):
    """
    Store instances
    * Detach data volumes from instances, create volume snapshots, create
      AMIs and terminate instances

    """
    instances = []
    if idle_only:
        # Get all idle instances
        instances = get_idle_instances(conn)
        if not instances:
            output.warning("There is no idle instance at this time.")
            return
    else:
        instances = get_instances(conn, True, "running")

    output.debug("The following idle instances will be stored.")
    list_instances_info(conn, instances)

    output.debug("Preparing to detach data volumes from instances...")
    volumes = get_data_volumes(conn, instances)
    volume_ids = [volume.id for volume in volumes]

    data = []

    # Read previous snapshots data if any
    rows = db.read_data(DB_FILES["snapshots"])
    data += rows

    source_snapshots = []

    for volume in volumes:
        # Detach the data volume and create snapshots
        instance_id = volume.attach_data.instance_id
        instance = get_instance(conn, instance_id)
        name = instance.tags.get("Name", "-")
        output.debug("Detaching data volume from instance %s..." % name)
        volume.detach()
        while volume.update() != "available":
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
        msg = "Creating snapshot of this volume..."
        output.debug(msg)
        snapshot = volume.create_snapshot()
        snapshot_id = snapshot.id

        if copy_snapshots:
            # Copy the snapshot to Amazon S3
            snapshot.update()
            if snapshot.status != "completed":
                time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
                snapshot.update()

            msg = "Copying the snapshot to Amazon S3..."
            output.debug(msg)

            snapshot_id = conn.copy_snapshot(EC2_DEFAULT_REGION,
                                             snapshot.id)
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)

            # Get the copied snapshot and make sure they are comleted
            copied_snapshot = conn.get_all_snapshots([snapshot_id])[0]
            copied_snapshot.update()
            if copied_snapshot.status != "completed":
                time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
                copied_snapshot.update()

            source_snapshots.append(snapshot)

        data.append([name, snapshot_id])

    db.write_data(DB_FILES["snapshots"], data)

    for instance in instances:

        name = instance.tags.get("Name", "-")

        image = conn.get_image(instance.image_id)
        if image:
            if image.id != EC2_DEFAULT_IMAGE_ID:
                msg = "Deleting old AMI of instance %s..." % name
                output.debug(msg)
                image.deregister()

        msg = "Creating AMI from instance %s..." % (name)
        output.debug(msg)
        image_id = instance.create_image(name)
        time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
        image = conn.get_image(image_id)
        while image.update() != "available":
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
        public_ip = instance.ip_address
        msg = "Disassociating public IP %s from instance %s..." % (name,
                                                                   instance.id)
        conn.disassociate_address(public_ip)
        # After AMI is created, terminate the instance
        msg = "Terminating instance %s (%s)..." % (name, instance.id)
        output.debug(msg)
        instance.terminate()

    output.debug("Waiting for all idle instances terminated before deleting "
                 "their data volumes...")

    for instance in instances:
        while instance.update() == "shutting-down":
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
        assert instance.update() == "terminated"

    delete_all_data_volumes(conn, volume_ids=volume_ids)
    if copy_snapshots:
        output.debug("Deleting source snapshots... ")
        for snapshot in source_snapshots:
            snapshot.delete()
    output.success("All instances are stored and backed up.")


def restore_instances(conn):
    """
    Restore instances
    * Launch instances from AMIs, create volume from volume snapshots, attach
      volumes to the instances
    """
    sg = get_security_group(conn)
    key_pair = get_key_pair(conn)
    snapshots = get_snapshots()

    images = conn.get_all_images(owners=["self"])
    image_name_mapping = {}  # Mapping of image name to instance id
    output.debug("Launching instances from this account's AMIs...")
    for image in images:
        reservation = image.run(
            min_count=1, max_count=1,
            security_groups=[sg.name], key_name=key_pair.name,
            instance_type=EC2_DEFAULT_INSTANCE_TYPE,
            placement=EC2_DEFAULT_EBS_AZ,
            monitoring_enabled=True)
        time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
        instance = reservation.instances[0]
        conn.create_tags([instance.id], {"Name": image.name})
        image_name_mapping[image.name] = instance.id

    instances = get_instances(conn, True, "pending")
    output.debug("Waiting for all instances running...")
    for instance in instances:
        while instance.update() == "pending":
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
        assert instance.update() == "running"

    instances = get_instances(conn, True, "running")

    addresses = get_addresses()
    output.debug("Associating public IPs into restored instances...")

    for instance in instances:
        name = instance.tags.get("Name", "-")
        ip = addresses[name]
        conn.associate_address(instance.id, ip)

    output.debug("Creating EBS data volumes from snapshots...")
    snapshots_dict = get_snapshots()
    snapshot_ids = [item for item in snapshots_dict]
    snapshots = conn.get_all_snapshots(snapshot_ids=snapshot_ids,
                                       owner="self")
    for snapshot in snapshots:
        volume = snapshot.create_volume(EC2_DEFAULT_EBS_AZ)
        while volume.update() != "available":
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
        name = snapshots_dict[snapshot.id]
        instanced_id = image_name_mapping[name]
        output.debug("Attaching EBS data volume for instance %s..." % name)
        volume.attach(instanced_id, EC2_DEFAULT_DATA_DEVICE)

    # Delete snapshots of data volumes
    delete_all_snapshots(conn, snapshot_ids)
    db.write_data(DB_FILES["snapshots"], [])


def autoscale_instances(conn):
    instances = get_instances(conn)
    for instance in instances:
        name = instance.tags.get("Name", "-")
        image_id = instance.image_id
        setup_autoscale_group(conn, name, image_id)


def stop_autoscale():
    groups = as_conn.get_all_groups()
    for group in groups:
        name = group.name
        delete_autoscale_group(conn, name)


def get_instances(conn, assert_num=False, state="running"):
    """Get all instances associated with this account"""
    all_instances = conn.get_only_instances()
    instances = []
    for instance in all_instances:
        if instance.state == state:
            instances.append(instance)
    if assert_num:
        # Confirm number of instances
        assert len(instances) == EC2_DEFAULT_INSTANCE_NUM
    return instances


def list_instances_info(conn, instances=None):
    if not instances:
        instances = get_instances(conn)
    print _format_line("Name", "Instance ID", "State", "CPU Util")
    print '-' * 60
    for instance in instances:
        name = instance.tags.get("Name", "-")
        instance_id = instance.id
        state = instance.state
        cpu_util = "%.2f" % get_cpu_stat(cw_conn, instance_id)
        print _format_line(name, instance_id, state, cpu_util)


def _format_line(*items):
    fmt = " {:{align}{width}}"
    line = ""
    for item in items:
        line += fmt.format(item, align="<", width=15)
    return line


def assign_tags(conn, instances, tags):
    assert len(instances) == len(tags)
    for i, instance in enumerate(instances):
        conn.create_tags([instance.id], {"Name": tags[i]})


def create_image(conn, instance):
    """Create AMI from a named instance"""
    name = instance.tags.get("Name")
    if name:
        conn.create_image(name)


def get_instance(get_instance, instance_id):
    instances = conn.get_only_instances(instance_ids=[instance_id])
    assert len(instances) == 1
    if instances:
        return instances[0]


def delete_all_images(conn):
    images = conn.get_all_images(owners=["self"])
    for image in images:
        image.deregister()


def get_idle_instances(conn, time_limit=0, cpu_limit=999999):
    """Get instances whose CPU utilization is less than 5 percent for
    for 10 minutes, or if it is after 5:00 p.m.
        time_limit is a number (0-24) representing 24-hour
    """
    instances = get_instances(conn)
    idle_instances = []
    now = datetime.datetime.now()
    if now.hour >= time_limit:
        output.debug("The current local time is after %d:00 p.m.. All"
                     " instances will be stored." % (time_limit - 12))
    for instance in instances:
        if now.hour >= time_limit:
            idle_instances.append(instance)
            continue
        cpu_util = get_cpu_stat(cw_conn, instance.id)
        if cpu_util < cpu_limit:
            name = instance.tags.get("Name", "-")
            fmsg = "Instance %s (%s) has an average CPU Utilization of %.2f%%."
            msg = fmsg % (name, instance.id, cpu_util)
            output.debug(msg)
            output.debug("This instance is to be stored.")
            idle_instances.append(instance)
    return idle_instances
