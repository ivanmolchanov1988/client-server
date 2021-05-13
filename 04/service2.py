def split(line, types=None, delimiter=None):
    fields = line.split(delimiter)
    if types:
        fields = [ ty(val) for ty, val in zip(types, fields) ]
    return fields