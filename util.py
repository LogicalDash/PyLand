def gentable(tabname, keydict, valdict, suffix=""):
    keynames = sorted(keydict.iterkeys())
    valnames = sorted(valdict.iterkeys())
    colnames = keynames + valnames
    coldict = {}
    coldict.update(keydict)
    coldict.update(valdict)
    coldecl = ", ".join(
        [colname + " " + coldict[colname] for colname in colnames])
    if suffix == "":
        return (keynames, valnames, colnames,
                "CREATE TABLE " + tabname + " (" + coldecl + ");")
    else:
        return (keynames, valnames, colnames,
                "CREATE TABLE " + tabname + " (" + coldecl
                + ", " + suffix + ");")


def genforeignkey(key_name, foreign_table, foreign_column):
    return "FOREIGN KEY(%s) REFERENCES %s(%s)" % (key_name,
                                                  foreign_table,
                                                  foreign_column)


def genforeignkeys(triples):
    return [genforeignkey(*trip) for trip in triples]


def genforeignkeystr(triples):
    return ", ".join(genforeignkeys(triples))
