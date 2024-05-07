import itertools

def keyfunc(line):
    return line.partition('\t')[0]