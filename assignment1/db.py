# I/O operations for locally stored data
import csv


def write_data(filename, rows):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def read_data(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        return list(reader)
