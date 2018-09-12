from . MoverDBs import ProjectID, StoPDB, StoPparts, Errors, FakeAccessions, OrigPathDups, PtoADB, PtoAFiles, PtoAError
from pathlib import Path
import os
from datetime import datetime
from tqdm import tqdm


class PathProvider:

    def __init__(self, item: StoPDB) -> None:
        self._item = item  # type: StoPDB
        self.paths = []  # type: str()
        self._current_ptaf = None  # type: PtoAFiles
        self._ptoadb = None  # type: PtoADB
        self.set_ptoadb()
        self._file_count = 0
        self.ptaf_items = []  # type: [PtoAFiles]

    def set_ptoadb(self):
        self._ptoadb, created = PtoADB.get_or_create(fk=self._item)

    def get_count(self) -> int:
        return self._file_count

    @property
    def ptoadb(self) -> PtoADB:
        return self._ptoadb

    @property
    def item(self) -> StoPDB:
        return self._item

    @property
    def current_ptaf(self) -> PtoAFiles:
        return self._current_ptaf

    @current_ptaf.setter
    def current_ptaf(self, i: PtoAFiles):
        self._current_ptaf = i

    def get_file_entries(self):
        print("Inspecting: \t{}".format(self._item.p_root))
        count = PtoAFiles.select().where(PtoAFiles.fk == self.ptoadb).count()

        if count > 0:
            query = PtoAFiles.select().where(PtoAFiles.fk == self.ptoadb, PtoAFiles.completed is False)
            self._file_count = len(query)
            if self._file_count == 0:
                self.close_item()
                return
            for item in query:  # type: PtoAFiles
                self.ptaf_items.append(item)
        else:
            p = Path("P:\\", self._item.p_root, 'data')
            path, dirs, files = os.walk(p).__next__()
            self._file_count = len(files)
            pbar = tqdm(total=self._file_count, ascii=True, desc="Adding to database: {}".format(p))
            for root, __, files in os.walk(p):
                for f in files:
                    fi = Path(root, f)
                    ptaf = PtoAFiles(fk=self.ptoadb, p_file_name=str(fi),
                                     p_file_size=fi.stat().st_size)
                    ptaf.save()
                    self.ptaf_items.append(ptaf)
                    pbar.update(1)
                    #print("Adding to database:\t{}".format(fi))
            pbar.close()

    def add_extra(self):
        p = Path("P:\\", self._item.p_root, 'data')
        path, dirs, files = os.walk(p).__next__()
        self._file_count = len(files)
        pbar = tqdm(total=self._file_count, ascii=True, desc="Adding to database: {}".format(p))
        for root, __, files in os.walk(p):
            for f in files:
                fi = Path(root, f)
                ptaf = PtoAFiles(fk=self.ptoadb, p_file_name=str(fi),
                                 p_file_size=fi.stat().st_size)
                try:
                    ptaf.save()
                except Exception as e:
                    print("Already Added.")
                    continue
                self.ptaf_items.append(ptaf)
                pbar.update(1)
                #print("Adding to database:\t{}".format(fi))
        pbar.close()

    def close_item(self):
        print("Closing: \t{}".format(self.item.p_root))
        query = (PtoAFiles.select().where(PtoAFiles.fk == self.ptoadb, PtoAFiles.completed is False))
        if query.exists():
            print("There are moves not completed. Cannot close this StopDB item.")
            return
        self.ptoadb.completed_conversion = True
        self.ptoadb.date_completed = datetime.now()
        self.ptoadb.save()
        self.item.a_complete = True
        self.item.save()