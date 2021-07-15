import os
from datetime import datetime
from pathlib import Path
from bulk_mover.move_db.move_provider import MoveProvider
from bulk_mover.move_db.PathProvider import PathProvider
from bulk_mover.move_db.MoverDBs import ProjectID, StoPDB, PtoADB, PtoAFiles, PtoAError
from bulk_mover.bulk_p2a import PMoverBase
from bulk_mover.mover_classes import PathMunger
from tqdm import tqdm


class FileCompare:

    def __init__(self, s_loc: Path, d_loc: Path) -> None:
        self._s_loc = s_loc  # type: Path
        self._d_loc = d_loc
        self.s_files = []
        self._not_copied = []

    def compare(self):
        print("Comparing paths.")
        for root, dirs, files in os.walk(self._s_loc):
            for f in files:
                p = Path(f).stem
                self.s_files.append(p)

        for root, dirs, files in os.walk(self._d_loc):
            for f in files:
                p = Path(f).stem
                if p in self.s_files:
                    self.s_files.remove(p)


class SqlPtoA(PMoverBase):
    def __init__(self, mp: MoveProvider) -> None:
        self.mp = mp
        self._current_items = []  # type: [StoPDB]
        self._current_item = None  # type: StoPDB
        self._current_ptadb = None  # type: PtoADB
        self._current_pta_item = None  # type: PtoAFiles

    def _write_success(self, pm: PathMunger):
        self._current_pta_item.a_file_name = pm.dest_file_path
        self._current_pta_item.a_file_size = os.path.getsize(pm.dest_file_path)
        self._current_pta_item.date_completed = datetime.now()
        self._current_pta_item.completed = True
        self._current_pta_item.save()

    def _write_fail(self, pm: PathMunger):
        pte, created = PtoAError.get_or_create(fk=self._current_pta_item, error_msg=pm.get_error())
        if created:
            pte.save()

    def move(self):
        for pp in self.get_path_provider():  # type: PathProvider
            pm = PathMunger.PathMunger(str(Path("P:\\", pp.item.p_root)), "A:")
            pbar = tqdm(total=pp.get_count(), ascii=True, desc="Converting: {}".format(pm.get_source_bag()))
            for ptaf in pp.ptaf_items:
                self._current_pta_item = ptaf
                pi = Path(ptaf.p_file_name)
                pm.set_current_targets(str(pi.parent), pi.parts[-1])
                pm.create_dest_path()
                if self._is_a_blank_path(pm.source_base):
                    if self._handle_restricted(pm):
                        self._write_success(pm)
                    else:
                        self._write_fail(pm)
                    pbar.update(1)
                    continue

                ext = pi.suffix
                if len(ext) < 4 or len(ext) > 5: #Checking the length of the the file extension. If extension is not 4 characters then complete transfer because we won't be able to tell what the filetype is.
                    # Extension will not be determinable go ahead and copy
                    if pm.do_a_copy():
                        self._write_success(pm)
                        pbar.update(1)
                        continue

                if pm.is_pass_through():
                    if pm.is_dest_there():
                        self._write_success(pm)
                        pbar.update(1)
                        continue
                    if pm.do_a_copy():
                        self._write_success(pm)
                        pbar.update(1)
                        continue
                    self._write_fail(pm)
                else:
                    if self._handle_conversion(pm):
                        self._write_success(pm)
                    else:
                        self._write_fail(pm)
                pbar.update(1)
            pbar.close()
            pp.close_item()

    def get_path_provider(self) -> [PathProvider]:
        self._current_items = self.mp.set_unfinished_items(self.mp.ATOP)
        for self._current_item in self._current_items:
            # is there PToAdb for this item?
            pp = PathProvider(self._current_item)
            # There is now. Are there files for this entry.
            pp.get_file_entries()
            #pp.add_extra()
            if len(pp.ptaf_items) == 0:
                continue
            # it does now
            yield pp

    def has_item_been_converted(self) -> bool:
        print("Checking for an existing path:\t{}".format(self._current_item.p_root))
        sp = Path("P:\\") / self._current_item.p_root / 'data'
        dp = Path("A:\\") / self._current_item.p_root
        spf = 0
        dpf = 0
        for root, dirs, files in os.walk(sp):
            spf += len(files)

        for root, dirs, files in os.walk(dp):
            dpf += len(files)

        if spf == dpf:
            return True
        return False


def new_file_chooser() -> MoveProvider:
    mp = MoveProvider()
    op = mp.set_open_projects(mp.ATOP)
    for i in op:  #type: ProjectID
        print("{}) {}".format(i.id, i.project_file))
    val = input("Select a project: ")
    mp.set_active_project(int(val))
    return mp


if __name__ == '__main__':
    mp = new_file_chooser()
    sqlmvr = SqlPtoA(mp)
    sqlmvr.move()
    if mp.ptoa_complete():
        mp.close_ptoa()
    print()