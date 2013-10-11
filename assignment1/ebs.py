# Elastic Block Store
from .settings import (EC2_DEFAULT_EBS_AZ, EC2_DEFAULT_EBS_SIZE,
                       EC2_DEFAULT_DATA_DEVICE, DB_FILES,
                       EC2_DEFAULT_INSTANCE_NUM)
from .utils import output
import db


def initialize_data_volume(conn):
    vol = conn.create_volume(size=EC2_DEFAULT_EBS_SIZE,
                             zone=EC2_DEFAULT_EBS_AZ)
    return vol


def get_snapshots():
    """
    Get snapshots of EBS data volumes
    * Return a dictionary mapping snapshot ids to virtual machine names
    """
    filename = DB_FILES["snapshots"]
    rows = db.read_data(filename)
    snapshots = {}
    if len(rows) > EC2_DEFAULT_INSTANCE_NUM:
        rows = rows[-EC2_DEFAULT_INSTANCE_NUM:]
    for row in rows:
        name = row[0]
        snapshot_id = row[1]
        snapshots[snapshot_id] = name
    return snapshots


def delete_all_data_volumes(conn, volume_ids=None):
    output.debug("Deleting data volumes...")
    volumes = conn.get_all_volumes(volume_ids=volume_ids)
    for volume in volumes:
        volume.delete()


def delete_all_snapshots(conn, snapshot_ids=None):
    output.debug("Deleting all snapshots....")
    snapshots = conn.get_all_snapshots(snapshot_ids=snapshot_ids)
    for snapshot in snapshots:
        conn.delete_snapshot(snapshot.id)


def get_data_volumes(conn, instances):
    """Get all data volumes from the specified instances"""
    volume_ids = []
    for instance in instances:
        bdm = instance.block_device_mapping
        bdt = bdm[EC2_DEFAULT_DATA_DEVICE]
        volume_id = bdt.volume_id
        volume_ids.append(volume_id)
    return conn.get_all_volumes(volume_ids=volume_ids)
