from __future__ import annotations

from procrastinate import exceptions


class ReadOnlyModel(exceptions.ProcrastinateException):
    pass
