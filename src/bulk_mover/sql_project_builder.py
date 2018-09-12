import sys
from pathlib import Path
from bulk_mover.move_db.MoverDBs import *
from datetime import datetime
from bulk_mover.mover_classes.Item import PItem


class SqlProjectBuilder:

    def __init__(self, project_file: str) -> None:
        self.project_file = Path(project_file)
        self.current_projid = None  # type: ProjectID
        self.current_stopd = None  # type: StoPDB
        self.lines_in_file = []  # type: [str]
        self.current_line = 3

    def create_project(self):
        try:
            self.current_projid, created = ProjectID.get_or_create(project_file=self.project_file,
                                                               project_added=datetime.now())  # type: ProjectID
        except IntegrityError as e:
            print("This file is already a project:\t{}".format(self.project_file))
            self.move_project_file()

    def _build_record(self, line: str):
        s = line.strip().split("\t")
        self.current_line += 1
        if len(s) <= 3:
            pi = PItem(s, True)  # type: PItem
        else:
            pi = PItem(s, False)  # type: PItem
        print("Adding to database: {}".format(pi.current_location))
        self.current_stopd = StoPDB(pid=self.current_projid)

        # Is there an old record
        old_record = StoPDB.select().where(StoPDB.p_root == pi.p_location and StoPDB.s_root == pi.current_location)

        if old_record.exists():
            # There is another s plus p record.  Record the error and continue
            print("Duplicated: {}".format(pi.current_location))
            dup_s_rec = StoPDB.get(StoPDB.s_root == pi.current_location)
            opd, created = OrigPathDups.get_or_create(sid_id=dup_s_rec, attempted_project=self.current_projid, attempted_line=self.current_line,
                               seen_before="{}{}{}".format(dup_s_rec.id, self.current_projid.get_id(), self.current_line))
            if created:
                opd.save()
            return

        self.current_stopd.p_root = pi.p_location
        self.current_stopd.s_root = pi.current_location
        self.current_stopd.save()

        if os.path.exists(pi.p_location):
            self.current_stopd.completed_move = True
            self.current_stopd.save()
        # Record the parts
        parts = StoPparts(root=self.current_stopd)
        parts.lvl1 = pi.record_status
        parts.lvl2 = pi.collection_type
        parts.lvl3 = self.get_padded_value(pi.record_group)
        parts.lvl4 = self.get_padded_value(pi.series)
        parts.lvl5 = self.get_padded_value(pi.item)
        parts.lvl6 = self.fix_accession_number(pi)
        parts.save()
        l = [parts.lvl1, parts.lvl2, parts.lvl3, parts.lvl4, parts.lvl5, parts.lvl6]
        new_p_root = os.path.sep.join([x for x in l if x is not None])
        self.current_stopd.p_root = new_p_root
        self.current_stopd.save()

    def fix_accession_number(self, pi: PItem):
        try:
            if len(pi.accession_number) != 9:
                if len(pi.accession_number.split("_")) == 2:
                    return pi.accession_number
                t = pi.accession_number[0]
                query = (FakeAccessions.select()
                         .where(FakeAccessions.fa_type == t)
                         .order_by(FakeAccessions.fa_num.desc())
                         )
                new_acc_num = None
                if query.exists():
                    inc = query.get()  # type: FakeAccessions
                    i = inc.fa_num
                    new_acc_num = i + 1
                else:
                    new_acc_num = 1

                new_acc_id = None
                if t == "F":
                    new_acc_id = t + "{0:8d}".format(new_acc_num)
                else:
                    new_acc_id = pi.accession_number + "{0:04d}".format(new_acc_num)

                fa = FakeAccessions(root=self.current_stopd, fa_type=t, fa_num=new_acc_num)
                fa.save()
                return new_acc_id
            return pi.accession_number
        except TypeError as e:
            return None

    def build_stopdb_lines(self):
        with open(self.project_file) as fh:
            for l in fh.readlines():
                if l[0] == "C":
                    continue
                self._build_record(l)
        self.move_project_file()

    def move_project_file(self):
        tg = Path(r"L:\Intranet\ar\Digital_Services\Inventory\000_ORIGINALS", self.project_file.name)
        self.project_file.rename(tg)
        sys.exit()

    def get_padded_value(self, v):
        try:
            i = int(v)
            return "{0:05d}".format(i)
        except ValueError as e:
            if v == '':
                return None
            return v
        except TypeError as e:
            return v


def file_chooser():
    base_path = r"L:\Intranet\ar\Digital_Services\Inventory\002_TO_BE_MOVED"
    my_files = []
    for root, dirs, files in os.walk(base_path):
        for f in files:
            my_files.append(os.path.join(root, f))
    for i in range(len(my_files)):
        i += 1
        print("{})\t{}".format(i, my_files[i - 1]))

    sel = input("Which file do you want to process: ")
    return my_files[int(sel) - 1]


if __name__ == '__main__':
    val = file_chooser()
    sqlpbldr = SqlProjectBuilder(val)
    sqlpbldr.create_project()
    sqlpbldr.build_stopdb_lines()
    print()
