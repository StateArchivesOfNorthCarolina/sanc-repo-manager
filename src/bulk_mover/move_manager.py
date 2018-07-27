import click
from pathlib import Path


if __name__ == '__main__':
    p = Path(r"P:\DS\AV\00005\00004\197508022\data")
    p.stat().count()