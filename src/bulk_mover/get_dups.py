from bulk_mover.move_db.MoverDBs import *
from pathlib import Path
import os
import re


def get_dups():
    query = StoPDB.raw("select *, count(p_root) as c from stopdb group by p_root having c > 1")
    with open("dup_report.txt", "w") as fh:
        for rec in query:
            new_q = StoPDB.select().where(StoPDB.p_root == rec.p_root)
            for n_rec in new_q:
                print("{}\t{}\t{}\t{}\n".format(n_rec.id, n_rec.pid_id, n_rec.p_root, n_rec.s_root))
                fh.write("{}\t{}\t{}\t{}\n".format(n_rec.id, n_rec.pid_id, n_rec.p_root, n_rec.s_root))


def fix_parts(project):
    query = (StoPparts
             .select(StoPparts, StoPDB)
             .join(StoPDB)
             .where(StoPparts.lvl2 is'AV')
             )
    for r in query:
        try:
            s = int(r.lvl4)
            print()
        except ValueError:
            print()
            r.lvl4 = r.lvl5
            r.lvl5 = r.lvl6
            r.lvl6 = None
            r.save()


class PathManager:

    def __init__(self) -> None:
        self._results = None


    @property
    def results(self):
        return self._results

    @results.setter
    def results(self, t):
        if t is None:
            self._results = StoPparts.select()
        elif isinstance(t, str):
            self._results = StoPparts.raw(t)
        else:
            self._results = StoPparts.select(StoPparts).where(self._get_type(t[0]) == t[1])

    def _get_type(self, v):
        if v == "lvl1":
            return StoPparts.lvl1
        if v == "lvl2":
            return StoPparts.lvl2
        if v == "lvl3":
            return StoPparts.lvl3
        if v == "lvl4":
            return StoPparts.lvl4
        if v == "lvl5":
            return StoPparts.lvl5
        if v == "lvl6":
            return StoPparts.lvl6


def build_paths():
    query = StoPparts.select()
    for r in query:
        p1 = r.lvl1
        p2 = r.lvl2
        p3 = None
        p4 = None
        p5 = None
        p6 = None
        try:
            p3 = "{0:05d}".format(int(r.lvl3))
        except ValueError:
            print()

        try:
            if r.lvl4 is not None:
                p4 = "{0:05d}".format(int(r.lvl4))
        except ValueError:
            print()

        try:
            if r.lvl5 is not None:
                p5 = "{0:05d}".format(int(r.lvl5))
        except ValueError:
            if r.lvl5[4] == "I":
                # This is a fake accession
                fa = FakeAccessions(r.id, int(r.lvl5.split("_")[1]))
            else:
                print()

        try:
            if r.lvl6 is not None:
                p6 = "{0:05d}".format(int(r.lvl5))
        except ValueError:
            print()

        try:
            parts = [p1, p2, p3, p4, p5, p6]
            p = os.path.sep.join([x for x in parts if x is not None])
            print(p)
        except AttributeError as e:
            print()
        except ValueError:
            print()


def join_path(lst):
    p = os.path.sep.join([x for x in lst if x is not None])
    return p


def get_sparts_join():
    results = (StoPDB
               .select()
               .where(StoPDB.s_root.contains('%.TIF'))
               .join(StoPparts))
    return results


def fix_lvl(f):
    if f:
        try:
            return "{0:05d}".format(int(f))
        except ValueError:
            return f
    return f


def fix_levels(r):
    r.lvl3 = fix_lvl(r.lvl3)
    r.lvl4 = fix_lvl(r.lvl4)
    r.lvl5 = fix_lvl(r.lvl5)
    return r


def fix_fake(r):
    fa = FakeAccessions()
    fa.root = r.root
    fa.save()
    r.lvl5 = "F{0:08d}".format(fa.id)
    return r


def get_raw_query():
    query = StoPDB.raw("SELECT s_root, p_root, COUNT(*) from stopdb GROUP BY p_root HAVING COUNT(*) > 1")
    return query


def test_parts():
    results = get_sparts_join()
    for r in results:
        r.delete_instance(recursive=True)


def remove_entries():
    stp = (StoPDB
           .select()
           .where(StoPDB.id == 314)
           .join(StoPparts))
    for s in stp:
        s.delete_instance(recursive=True)


if __name__ == '__main__':
    remove_entries()