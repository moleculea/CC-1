from nose.tools import *
from assignment1.conn import conn
from assignment1.cw import get_cpu_stat, cw_conn
from assignment1.instances import list_instances_info, get_instances


def test_list_instances_info():
    num1 = list_instances_info(conn)
    num2 = len(get_instances(conn))
    assert_equal(num1, num2)


def test_get_cpu_stat():
    instances = get_instances(conn)
    for instance in instances:
        util = get_cpu_stat(cw_conn, instance.id)
        assert 0 <= util and util <= 200
