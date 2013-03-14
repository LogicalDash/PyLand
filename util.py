def iterdict(keydict):
    r = []
    for key in keydict.iterkeys():
        if keydict[key] == '':
            r.append(key)
        else:
            r.append(key + ' ' + keydict[key])
    return r


def genschema(tabname, keydict, valdict, suffix=""):
    ikeydict = iterdict(keydict)
    ivaldict = iterdict(valdict)
    if suffix == "":
        final_comma = ""
    else:
        final_comma = ", "
    return ("CREATE TABLE " + tabname + " (" + ", ".join(ikeydict + ivaldict)
            + final_comma + suffix + ");")


def genforeignkey(key_name, foreign_table, foreign_column):
    return "FOREIGN KEY(%s) REFERENCES %s(%s)" % (key_name,
                                                  foreign_table,
                                                  foreign_column)


def genforeignkeys(triples):
    return [genforeignkey(*trip) for trip in triples]


def genforeignkeystr(triples):
    return ", ".join(genforeignkeys(triples))
