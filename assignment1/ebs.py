# Elastic Block Store
from .settings import (EC2_DEFAULT_EBS_AZ, EC2_DEFAULT_EBS_SIZE,
                       EC2_DEFAULT_DATA_DEVICE, DB_FILES)
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
    for row in rows:
        name = row[0]
        snapshot_id = row[1]
        snapshots[snapshot_id] = name
    return snapshots


def delete_data_volumes(conn):
    output.debug("Deleting data volumes...")
    volumes = conn.get_all_volumes()
    for volume in volumes:
        if volume.attach_data.device == EC2_DEFAULT_DATA_DEVICE:
            volume.delete()


def delete_all_snapshots(conn):
    output.debug("Deleting all snapshots....")
    snapshots = conn.get_all_snapshots()
    for snapshot in snapshots:
        if snapshot.status == "status":
            conn.delete_snapshot(snapshot.id)
