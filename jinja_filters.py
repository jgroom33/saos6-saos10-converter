def hyphen_range_to_list(s):
    """
    yield each integer from a complex range string like "1-9,12, 15-20,23"

    Original

    "1-9,12, 15-20,23"

    Returned Array

    [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 16, 17, 18, 19, 20, 23]
    """

    def hyphen_range(s):
        for x in s.split(","):
            elem = x.split("-")
            if len(elem) == 1:  # a number
                yield int(elem[0])
            elif len(elem) == 2:  # a range inclusive
                start, end = map(int, elem)
                for i in range(start, end + 1):
                    yield i
            else:  # more than one hyphen
                raise ValueError("format error in %s" % x)

    return list(hyphen_range(s))


def merge_table_by_key(table, table_key):
    """
    Merge the contents of a table based on the key of that table.  This assumes that properties in the rows being merged do not overlap. Example:

    Original

    | key | foo | bar | baz |
    | --- | --- | --- | --- |
    | 1   | a   |     |     |
    | 1   |     | b   | c   |
    | 2   | a   |     |     |

    Merged

    | key | foo | bar | baz |
    | --- | --- | --- | --- |
    | 1   | a   | b   | c   |
    | 2   | a   |     |     |
    """
    result = {}
    for row in table:
        if row[table_key] in result:
            for (key, value) in row.items():
                if value != "":
                    result[row[table_key]][key] = value
        else:
            result[row[table_key]] = row
    return list(result.values())


def table_flatten(table):
    """
    Merge ALL the rows of a table into a single item. This assumes there is no property overlap

    | key | foo | bar | baz |
    | --- | --- | --- | --- |
    | 1   | a   |     |     |
    |     |     | b   |     |
    |     |     |     | z   |

    Merged

    | key | foo | bar | baz |
    | --- | --- | --- | --- |
    | 1   | a   | b   | c   |

    """
    result = {}
    for (key, value) in table[0].items():
        result[key] = ""
    for row in table:
        for (key, value) in row.items():
            if value != "":
                result[key] = value
    return [result]
