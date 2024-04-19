from sqlalchemy import asc, desc, nulls_first
from sqlalchemy import nulls_last


def asc_(column):
    return nulls_first(asc(column))


def desc_(column):
    return nulls_last(desc(column))
