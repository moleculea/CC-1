import os
import sys


class output(object):
    """
    ANSI console colored output:
        * error (red)
        * warning (yellow)
        * debug (green)

    Set environment variable `COLOR_OUTPUT_VERBOSE' to enable debug
    """

    RED     = 1
    GREEN   = 2
    YELLOW  = 3
    ERROR   = 4
    DEBUG   = 5
    WARNING = 6
    SUCCESS = 7

    @staticmethod
    def __out(type, msg):
        if type == output.ERROR:
            sys.stderr.write("\033[%dm [%s] %s\033[m\n" %
                            (30 + output.RED, "Error", msg))

        if type == output.DEBUG:
            sys.stdout.write("\033[%dm [%s] %s\033[m\n" %
                            (30 + output.GREEN, "Debug", msg))

        if type == output.WARNING:
            sys.stdout.write("\033[%dm [%s] %s\033[m\n" %
                            (30 + output.YELLOW, "Warning", msg))

        if type == output.SUCCESS:
            sys.stdout.write("\033[%dm [%s] %s\033[m\n" %
                            (30 + output.GREEN, "Sucess", msg))

    @staticmethod
    def error(msg):
        output.__out(output.ERROR, msg)

    @staticmethod
    def debug(msg):
        if "COLOR_OUTPUT_VERBOSE" in os.environ:
            output.__out(output.DEBUG, msg)

    @staticmethod
    def warning(msg):
        output.__out(output.WARNING, msg)

    @staticmethod
    def success(msg):
        output.__out(output.SUCCESS, msg)
