from .utils import output
from .settings import DB_FILES
import db
import os


def initialize_address(conn):
    address = conn.allocate_address()
    return address.public_ip


def assign_addresses(conn, instances):
    """
    Assign addresses for the first time
    * Associate newly allocated addresses to instances
    * Store mapping of each instance to addresses (name to public IPs)
    """
    data = []
    for instance in instances:
        public_ip = initialize_address(conn)
        conn.associate_address(instance.id, public_ip)
        instance.update()  # Update assigned tags
        name = instance.tags.get("Name", "-")
        data.append([name, public_ip])
    filename = DB_FILES["addresses"]
    db.write_data(filename, data)


def get_addresses():
    """
    Get public IPs
    * Return a dictionary mapping virtual machine names to previously
      associated public IPs

    """
    filename = DB_FILES["addresses"]
    rows = db.read_data(filename)
    addresses = {}
    for row in rows:
        name = row[0]
        ip = row[1]
        addresses[name] = ip
    return addresses


def release_all_addresses(conn):
    output.debug("Releasing all elastic IPs...")
    all_addresses = conn.get_all_addresses()
    for address in all_addresses:
        if not address.instance_id:
            address.release()
