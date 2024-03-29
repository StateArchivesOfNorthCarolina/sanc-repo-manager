"""
This is now the main program.  It co-ordinates sql_project_builder, sql_mover, sql_ptoa, and sql_cleanup
"""
import os
import sys
import tkinter as tk
from tkinter import filedialog
from bulk_mover.sql_project_builder import SqlProjectBuilder
from bulk_mover.move_db.move_provider import MoveProvider
from bulk_mover.sql_mover import SqlMover
from bulk_mover.sql_ptoa import SqlPtoA
from bulk_mover.move_db.MoverDBs import ProjectID
from bulk_mover.sql_cleanup import SqlCleanup


class Builder:

    def file_chooser(self):#Finds all the files from a move folder and preps for movement to the p drive
        
        base_path = getFileDirectory()

        #base_path = r"C:\Users\lospa\Downloads\Move_db_samples\Move_db_samples" #CHANGE THIS TO AN ADDRESS REQUEST
        my_files = []
        for root, dirs, files in os.walk(base_path):
            for f in files:
                my_files.append(os.path.join(root, f))

        if len(my_files) == 0:
            print("No projects to add.")
            return

        for i in range(len(my_files)):
            i += 1
            print("{})\t{}".format(i, my_files[i - 1]))

        print("Q)\tQuit")

        sel = input("Which file do you want to process: ")

        if sel.lower() == 'q':
           goBackToMenu()

        return my_files[int(sel) - 1]

    def run(self):
        val = self.file_chooser()
        if val is None:
            return
        sqlpbldr = SqlProjectBuilder(val)#Located in sql_project_builder.py
        sqlpbldr.create_project()
        #sqlpbldr.build_stopdb_lines() Moved this into the create_project function inside of sql_project_builder
        goBackToMenu()


class Mover:

    def file_chooser(self):
        mp = MoveProvider()#points at move_provider.py
        op = mp.set_open_projects(mp.STOP)
        c = 1
        if len(op) == 0:
            print("No projects to move.")
            return False, mp

        for i in op:  # type: ProjectID
            print("{}) {}".format(i.get_id(), i.project_file))
            c += 1
        print("Q)\tQuit")

        val = input("Select a project: ")

        if val.lower() == 'q':
            goBackToMenu()

        if val is None:
            goBackToMenu()

        mp.set_active_project(int(val))
        return True, mp

    def run(self):
        while True:
            stp, mp = self.file_chooser()
            if stp:
                print()
                sqlmvr = SqlMover(mp) #references in sql_mover.py
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

        print("Q)\tQuit")
        val = input("Select a project: ")

        if val.lower() == 'q':
            goBackToMenu()

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
                   ) #This query requires '==' instead of 'is False'
        for prj in project:  # type: ProjectID
            print("{})\t{}".format(prj.id, prj.project_file))
            prjs.append(prj)
        print("Q)\tQuit")

        if len(prjs) == 0:
            return None

        val = input("Which project do you want to cleanup? ")

        if val.lower() == 'q':
            return None

        pro = ProjectID.get(ProjectID.id == int(val))
        return pro

    def run(self):
        #adjusted this file to fail gracefully back to menu instead of hard crash.
        #file checks if the program found any items to be cleaned up. If not, it returns to the menu otherwise it runs the cleanup program.
        sqlc = self.project_select()

        if sqlc is None:
            return

        sqlc = SqlCleanup(sqlc)

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

def getFileDirectory(): # Sets up file directory window to allow path selection
    root = tk.Tk()
    root.withdraw()

    directoryLocation = filedialog.askdirectory(parent=root, title='Choose directory where files are located')
    root.destroy()

    return directoryLocation

def goBackToMenu(): #Functions as a callable return to the main menu
        menu = Coordinator()
        menu.menu()