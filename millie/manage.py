#!/usr/bin/env python
import pymysql

pymysql.install_as_MySQLdb()

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django를 찾을 수 없습니다. 가상환경이 활성화돼 있는지 확인하세요."
        ) from exc
    execute_from_command_line(sys.argv)