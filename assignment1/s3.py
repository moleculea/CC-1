from boto.s3.connection import S3Connection
from boto.s3.key import Key
import sys


from .settings import S3_DEFAULT_BUCKET
from .utils import output, get_absolute_path


s3_conn = S3Connection()


def create_bucket():
    bucket = s3_conn.create_bucket(S3_DEFAULT_BUCKET)
    return bucket


def get_bucket():
    bucket = s3_conn.lookup(S3_DEFAULT_BUCKET)
    if bucket:
        return bucket
    return create_bucket(name)


def store_object(key, filename):
    bucket = get_bucket()
    k = Key(bucket)
    k.key = key
    f = get_absolute_path(filename)
    k.set_contents_from_filename(f)
    msg = "File %s has been stored with key '%s' to bucket '%s'." %(filename,
                                                                key,
                                                                bucket.name)
    output.success(msg)


def get_object(key, filename):
    bucket = get_bucket()
    k = bucket.get_key(key)
    if not k:
        msg = "Key '%s' does not exist in bucket '%s'." % (key, bucket.name)
        output.error(msg)
        sys.exit(1)
    f = get_absolute_path(filename)
    k.get_contents_to_filename(f)
    fmsg = ("Object with key '%s' has been stored to"
            " %s from bucket '%s'.")
    msg = fmsg % (key, filename, bucket.name)
    output.success(msg)


def print_object(key):
    bucket = get_bucket()
    k = bucket.get_key(key)
    if not k:
        msg = "Key '%s' does not exist in bucket '%s'." % (key, bucket.name)
        output.error(msg)
        sys.exit(1)
    print k.get_contents_as_string()


def s3_init():
    msg = "Initializing bucket named '%s'..." % S3_DEFAULT_BUCKET
    output.debug(msg)
    bucket = s3_conn.lookup(S3_DEFAULT_BUCKET)
    if bucket:
        fmsg = "Bucket '%s' already exists. Creation aborted."
        msg = fmsg % S3_DEFAULT_BUCKET
        output.warning(msg)
        sys.exit(0)
    create_bucket()
    msg = "Bucket '%s' created..." % S3_DEFAULT_BUCKET
    output.debug(msg)


def s3_put():
    print "Key name: "
    key = raw_input()
    print "File to put: "
    filename = raw_input()
    store_object(key, filename)


def s3_get():
    print "Key name: "
    key = raw_input()
    print "Output file: "
    filename = raw_input()
    get_object(key, filename)


def s3_print():
    print "Key name: "
    key = raw_input()
    print_object(key)
