from pathlib import Path
from move_db.MoverDBs import StoPDB


def stop_index_report():
    p = Path("a_drive_index.tsv")
    if not p.exists():
        p.touch()

    q = (StoPDB
         .select(StoPDB.s_root, StoPDB.p_root))
    with p.open(mode='w') as fh:
        fh.write("Former_Location\tAccess_Drive\n")
        for i in q:
            print(f"{i.s_root}\t{i.p_root}")
            fh.write(f"{i.s_root}\t{i.p_root}\n")


if __name__ == '__main__':
    stop_index_report()