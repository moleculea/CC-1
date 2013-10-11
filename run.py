import os
import sys

from assignment1.conn import conn
from assignment1.instances import (list_instances_info, initialize_instances,
                                   store_instances, restore_instances,
                                   autoscale_instances, stop_autoscale,
                                   flush_db)
from assignment1.cw import cw_conn, get_cpu_stat
from assignment1.utils import output


CMD_USAGE = "Usage: python run.py init|store|restore|list|scale|nscale"
INVALID_USAGE = ("Invalid Argument: '%s'. Must be" 
                 " init|store|store-s3|store-force|restore|list|scale|nscale"
                 "|flushdb")

CTRL_ARGS = {
    "init": "initialize_instances(conn)",
    "store": "store_instances(conn, False, True)",
    "store-s3": "store_instances(conn, True, True)",
    "store-force": "store_instances(conn)",
    "restore": "restore_instances(conn)",
    "list": "list_instances_info(conn)",
    "scale": "autoscale_instances(conn)",
    "nscale": "stop_autoscale()",
    "flushdb": "flush_db()",
}


def main():
    cmd()


def cmd():
    if len(sys.argv) != 2:
        print CMD_USAGE
        sys.exit(1)
    arg = sys.argv[1]

    if arg in ["-h", "--help"]:
        print CMD_USAGE
        sys.exit(0)

    if arg in CTRL_ARGS:
        statement = CTRL_ARGS[arg]
        eval(statement)
    else:
        output.error(INVALID_USAGE % arg)
        sys.exit(1)


if __name__ == "__main__":

    # Setting default output mode to verbose
    os.environ["COLOR_OUTPUT_VERBOSE"] = "1"
    main()
