from assignment1.conn import conn
from boto.ec2.blockdevicemapping import BlockDeviceMapping, BlockDeviceType
def main():

    rs = conn.get_all_security_groups()
    print rs
    vols = conn.get_all_volumes()
    print vols
    for vol in vols:
        print vol.attach_data.device

    #dev_sda1 = BlockDeviceType(snapshot_id="snap-6a6b5669")  # root volume
    #dev_sdf = BlockDeviceType(snapshot_id="snap-bd2310be")  # data volume
    #bdm = BlockDeviceMapping()
    #bdm["/dev/sda1"] = dev_sda1
    #bdm["/dev/xvdf"] = dev_sdf

    #conn.register_image(name="CC-AMI-3", root_device_name="/dev/sda1", block_device_map=bdm)

    conn.create_image(instance_id="i-bbfda8c2", name="CC-AMI-4")


if __name__ == "__main__":
    main()
