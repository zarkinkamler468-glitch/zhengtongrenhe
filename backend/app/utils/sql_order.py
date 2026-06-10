from sqlalchemy import ColumnElement


def desc_nulls_last(column: ColumnElement) -> tuple[ColumnElement, ColumnElement]:
    """MySQL 兼容：降序且空值排在最后（等价于 PostgreSQL 的 DESC NULLS LAST）。"""
    return column.is_(None), column.desc()
