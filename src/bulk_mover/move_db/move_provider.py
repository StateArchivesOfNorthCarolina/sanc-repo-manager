import os
from pathlib import Path
from move_db.MoverDBs import ProjectID, StoPDB, StoPparts, Errors, FakeAccessions, OrigPathDups, PtoADB, PtoAFiles, PtoAError


class MoveProvider:
    STOP = 1
    ATOP = 2

    def __init__(self) -> None:
        self.open_projects = []  # type: [ProjectID]
        self.active_project = None  # type: ProjectID
        self.unfinished_items = []  # type: [StoPDB]
        self.active_item = None  # type: StoPDB

    def set_open_projects(self, t: int) -> [ProjectID]:
        if len(self.open_projects) == 0:
            if t == MoveProvider.STOP:
                for q in ProjectID.select().where(ProjectID.stop_complete == False):
                    self.open_projects.append(q)

            if t == MoveProvider.ATOP:
                for q in ProjectID.select().where(ProjectID.ptoa_complete == False):
                    self.open_projects.append(q)
        return self.open_projects

    def set_active_project(self, p: int):
        self.active_project = ProjectID.get(ProjectID.id == p)
        print("Setting Project to: \t{}".format(self.active_project.project_file))

    def set_unfinished_items(self, t: int) -> [StoPDB]:
        if t == MoveProvider.STOP:
            for item in StoPDB.select().where((StoPDB.pid == self.active_project) &
                                              (StoPDB.completed_move == False) &
                                              (StoPDB.skip == False)):
                self.unfinished_items.append(item)

        if t == MoveProvider.ATOP:
            for item in StoPDB.select().where((StoPDB.pid == self.active_project) &
                                              (StoPDB.completed_move == True) &
                                              (StoPDB.a_complete == False)):
                self.unfinished_items.append(item)

        return self.unfinished_items

    def close_stop(self):
        print("Closing S To P for: \t{}".format(self.active_project.project_file))
        self.active_project.stop_complete = True
        self.active_project.save()

    def close_project(self):
        self.active_project.project_completed = True
        self.active_project.stop_complete = True
        self.active_project.save()

    def close_ptoa(self):
        self.active_project.ptoa_complete = True
        self.active_project.save()

    def ptoa_complete(self):
        for i in self.unfinished_items:  # type: StoPDB
            if not i.a_complete:
                return False
        return True

    def can_close_item(self):
        pass


if __name__ == '__main__':
    pass