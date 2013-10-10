# Virtual machine operations
import time


from .addr import assign_addresses, get_addresses
from .conn import conn
from .ebs import (initialize_data_volume, get_snapshots, delete_all_snapshots,
                  delete_data_volumes)
from .keys import get_key_pair
from .settings import (EC2_DEFAULT_INSTANCE_TYPE, EC2_DEFAULT_IMAGE_ID,
                       EC2_DEFAULT_INSTANCE_NUM, EC2_DEFAULT_TAG_NAMES,
                       EC2_DEFAULT_WAIT_INTERVAL, EC2_DEFAULT_DATA_DEVICE,
                       EC2_DEFAULT_REGION, DB_FILES, EC2_DEFAULT_EBS_AZ)
from .sg import get_security_group
from .utils import output
import db


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


def store_instances(conn, copy_snapshots=False):
    """
    Store instances
    * Detach data volumes from instances, create volume snapshots, create
      AMIs and terminate instances
    """
    output.debug("Preparing to detach data volumes from instances...")
    volumes = conn.get_all_volumes()
    data = []
    for volume in volumes:
        # Detach the data volume and create snapshots
        if volume.attach_data.device == EC2_DEFAULT_DATA_DEVICE:
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
            if copy_snapshots:
                # Copy the snapshot to Amazon S3
                msg = "Copying the snapshot to Amazon S3..."
                outout.debug(msg)
                snapshot = conn.copy_snapshot(EC2_DEFAULT_REGION,
                                              snapshot.id)
            data.append([name, snapshot.id])

    assert len(data) == EC2_DEFAULT_INSTANCE_NUM

    db.write_data(DB_FILES["snapshots"], data)
    instances = get_instances(conn, True, "running")

    for instance in instances:
        name = instance.tags.get("Name", "-")
        msg = "Creating AMI from instance %s..." % (name)
        output.debug(msg)
        image_id = instance.create_image(name)
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

    output.debug("Waiting for all instances terminated before deleting "
                 "data volumes...")
    for instance in instances:
        while instance.update() == "shutting-down":
            time.sleep(EC2_DEFAULT_WAIT_INTERVAL)
        assert instance.update() == "terminated"
    delete_data_volumes(conn)
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

    delete_all_images(conn)
    delete_all_snapshots(conn)


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


def list_instances_info(conn):
    instances = get_instances(conn)
    print _format_line("Name", "Instance ID", "State", "Monitor")
    print '-' * 60
    for instance in instances:
        name = instance.tags.get("Name", "-")
        instance_id = instance.id
        state = instance.state
        monitored = instance.monitored
        print _format_line(name, instance_id, state, monitored)


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
    """Create AMI from an instance"""
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
