from pathlib import Path
from bulk_mover.move_db.MoverDBs import StoPDB


def stop_index_report():
    p = Path("a_drive_index.tsv") #fileName for report
    if not p.exists(): #Check to see if file already exists, and if it does not, create it
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