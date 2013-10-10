import os
import datetime
from assignment1.conn import conn
from assignment1.instances import (list_instances_info, initialize_instances,
                                   store_instances, restore_instances)
from assignment1.settings import DB_PATH, PROJECT_PATH

def main():
    #initialize_instances(conn)
    store_instances(conn)
    #restore_instances(conn)
    list_instances_info(conn)


if __name__ == "__main__":
    os.environ["COLOR_OUTPUT_VERBOSE"] = "1"
    main()
