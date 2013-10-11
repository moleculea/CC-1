import os
import sys

from assignment1.conn import conn
from assignment1.instances import (list_instances_info, initialize_instances,
                                   store_instances, restore_instances,
                                   autoscale_instances, stop_autoscale)
from assignment1.settings import DB_PATH, PROJECT_PATH
from assignment1.cw import cw_conn, get_cpu_stat
from assignment1.utils import output


CMD_USAGE = "Usage: python run.py init|store|restore|list|scale|nscale"
INVALID_USAGE = ("Invalid Argument: '%s'. Must be" 
                 " init|store|restore|list|scale|nscale")

CTRL_ARGS = {
    "init": "initialize_instances(conn)",
    "store": "store_instances(conn, True, True)",
    "restore": "restore_instances(conn)",
    "list": "list_instances_info(conn)",
    "scale": "autoscale_instances(conn)",
    "nscale": "stop_autoscale()"
}


def main():
    #initialize_instances(conn)
    #list_instances_info(conn)
    #store_instances(conn, True, True)
    #restore_instances(conn)
    #list_instances_info(conn)
    #print get_cpu_stat(cw_conn, "i-2f410248", 2)
    #autoscale_instances(conn)
    #stop_autoscale()
    cmd()


def cmd():
    if len(sys.argv) != 2:
        print CMD_USAGE
        sys.exit(1)
    arg = sys.argv[1]
    if arg in CTRL_ARGS:
        statement = CTRL_ARGS[arg]
        eval(statement)
    else:
        output.error(INVALID_USAGE % arg)


if __name__ == "__main__":
    os.environ["COLOR_OUTPUT_VERBOSE"] = "1"
    main()
