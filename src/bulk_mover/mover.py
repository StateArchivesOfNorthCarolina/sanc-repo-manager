"""
This is now the main program.  It co-ordinates sql_project_builder, sql_mover, sql_ptoa, and sql_cleanup
"""
import os
import sys
from sql_project_builder import SqlProjectBuilder
from move_db.move_provider import MoveProvider
from sql_mover import SqlMover
from sql_ptoa import SqlPtoA
from move_db.MoverDBs import ProjectID
from sql_cleanup import SqlCleanup



class Builder:

    def file_chooser(self):
        base_path = r"L:\Intranet\ar\Digital_Services\Inventory\002_TO_BE_MOVED"
        my_files = []
        for root, dirs, files in os.walk(base_path):
            for f in files:
                my_files.append(os.path.join(root, f))
        for i in range(len(my_files)):
            i += 1
            print("{})\t{}".format(i, my_files[i - 1]))

        if len(my_files) == 0:
            print("No projects to add.")
            return

        sel = input("Which file do you want to process: ")
        return my_files[int(sel) - 1]

    def run(self):
        val = self.file_chooser()
        if val is None:
            return
        sqlpbldr = SqlProjectBuilder(val)
        sqlpbldr.create_project()
        sqlpbldr.build_stopdb_lines()


class Mover:

    def file_chooser(self):
        mp = MoveProvider()
        op = mp.set_open_projects(mp.STOP)
        c = 1
        if len(op) == 0:
            print("No projects to move.")
            return False, mp

        for i in op:  # type: ProjectID
            print("{}) {}".format(i.get_id(), i.project_file))
            c += 1
        val = input("Select a project (q to quit): ")
        if val != "q" or val is None:
            mp.set_active_project(int(val))
            return True, mp
        else:
            return False, mp

    def run(self):
        while True:
            stp, mp = self.file_chooser()
            if stp:
                print()
                sqlmvr = SqlMover(mp)
                sqlmvr.move_items()
                print()
                print()
            else:
                break


class PTOA:

    def file_chooser(self) -> MoveProvider:
        mp = MoveProvider()
        op = mp.set_open_projects(mp.ATOP)
        if len(op) == 0:
            return
        for i in op:  #type: ProjectID
            print("{}) {}".format(i.id, i.project_file))
        val = input("Select a project: ")
        mp.set_active_project(int(val))
        return mp

    def run(self):
        mp = self.file_chooser()
        if mp is None:
            return
        sqlmvr = SqlPtoA(mp)
        sqlmvr.move()
        if mp.ptoa_complete():
            mp.close_ptoa()


class Cleanup:

    def project_select(self) -> ProjectID:
        prjs = []
        project = (ProjectID
                   .select()
                   .where((ProjectID.project_completed == False))
                   )
        for prj in project:  # type: ProjectID
            print("{})\t{}".format(prj.id, prj.project_file))
            prjs.append(prj)

        if len(prjs) == 0:
            return
        val = input("Which project do you want to cleanup? ")
        pro = ProjectID.get(ProjectID.id == int(val))
        return pro

    def run(self):
        sqlc = SqlCleanup(self.project_select())
        if sqlc is None:
            return
        sqlc.check_stopdbs()


class Coordinator:

    def menu(self):
        print("\n\nWhat do you want to do?")
        print("\n"
              "1) Open a project. (This means you have a spreadsheet that is not part of the project list)\n"
              "2) Move project items from Origin to final P: location?\n"
              "3) Cleanup Origin locations? \n"
              "4) Transform repository location to an access location? \n"
              "5) Quit\n")
        val = None
        try:
            val = int(input("Enter a number: "))
        except TypeError as e:
            print("You must enter a number 1-5")
            self.menu()

        if val == 1:
            b = Builder()
            b.run()
            self.menu()
        if val == 2:
            m = Mover()
            m.run()
            self.menu()
        if val == 3:
            c = Cleanup()
            c.run()
            self.menu()
        if val == 4:
            t = PTOA()
            t.run()
            self.menu()
        if val == 5:
            sys.exit(0)


if __name__ == '__main__':
    coord = Coordinator()
    coord.menu()