import os
import sys
from datetime import date, datetime

import stat
from shutil import rmtree
import yaml
import logging
import logging.config
from bagit import BagValidationError
import time

from bulk_mover.mover_classes.Item import PItem
from bulk_mover.mover_classes.SANCBagger import SANCBagger
from bulk_mover.mover_classes.CopyProgress import CopyProgress
from bulk_mover.mover_classes.PathUnique import PathUnique
from bulk_mover.move_db.MoverDBs import ProjectID, StoPDB, StoPparts, Errors, FakeAccessions, OrigPathDups
from bulk_mover.move_db.move_provider import MoveProvider


class SqlMover:

    def __init__(self, move_provider: MoveProvider) -> None:
        self._mp = move_provider
        self._items = []  # type: [StoPDB]
        self._current_item = None  # type: StoPDB
        self._p_path_exists = False
        self._s_path_exists = False
        self._p_valid = False
        self._s_valid = False
        self._error_message = ''
        self._bag_details = ''

    def _check_bag(self, p: str, location: str) -> bool:
        item = None
        if location == "D":
            item = self._get_path_as_p()
            if self._current_item.p_validated_on is not None:
                return True
        if location == "O":
            item = self._current_item.s_root
            if self._current_item.s_validated_on is not None:
                return True

        sb = SANCBagger(p)
        if sb.open_bag():
            print("Validating: \t{}".format(item))
            if sb.fast_validate_bag():
                print("Valid.")
                return True
        print("Not Valid.")
        self._error_message = sb.bagging_error
        self._bag_details = sb.validation_error_details
        return False

    def _get_path_as_p(self):
        return os.path.join("P:\\", self._current_item.p_root)

    def _check_p(self):
        if self._current_item.p_validated_on is not None:
            return True
        if self._check_path(self._get_path_as_p()):
            print("Path exists at the destination")
            # The path exists on P
            self._p_path_exists = True
            if self._check_bag(self._get_path_as_p(), "D"):
                # Bag on P is valid. This is a valid and complete move.
                self._current_item.p_validated_on = datetime.now()
                self._current_item.completed_move = datetime.now()
                self._current_item.save()
                self._p_valid = True
                return True
            # Bag on P is not valid.  Does S: exist and is it valid?
        return False

    def _check_s(self):
        if self._check_path(self._current_item.s_root):
            # The S path exists. Check if there is a bag.
            self._s_path_exists = True
            if self._check_bag(self._current_item.s_root, "O"):
                # The S Path bag exists and is valid
                self._current_item.s_validated_on = datetime.now()
                self._s_valid = True
                return True
        return False

    def _check_bags(self) -> bool:
        print("Validating Bags.")
        if self._check_p():
            self._current_item.p_validated_on = datetime.now()
            self._current_item.save()
            return True

        if self._check_s():
            self._current_item.s_validated_on = datetime.now()
            self._current_item.save()
            return True

        return False

    def _try_to_bag(self):
        meta = {
            "Contact-Name": "Jeremy Gibson",
            "Source-Organization": "State Archives of North Carolina",
            "Internal-Sender-Identifier": "SqlMover 0.0.1"
        }
        b = os.path.join(self._current_item.s_root, "data")
        if not os.path.exists(b):
            sb = SANCBagger()
            if sb.create_bag(self._current_item.s_root, meta):
                self._current_item.is_bagged = True
                self._current_item.save()
                return True
            return False

    def _do_copy_to_destination(self):
        print("Copying to:\t{}".format(self._get_path_as_p()))
        try:
            cp = CopyProgress("\\\\?\\" + self._current_item.s_root, self._get_path_as_p(), CopyProgress.FILES)
            cp.start_copy()
            return True
        except Exception as e:
            print(e)
            self._write_error(str(e))
            return False

    def _prep_copy_to_destination(self):
        # Create the path
        if self._do_copy_to_destination():
            # We've moved it.  Validate.
            if self._check_bag(self._get_path_as_p(), "D"):
                # It's valid.  Mark as complete.
                self._current_item.completed_move = True
                self._current_item.p_validated_on = datetime.now()
                self._current_item.save()
            else:
                # Not Valid. Set error.
                print("Destination location did not validate after move: {}".format(self._current_item.s_root))
                self._write_error("Destination location did not validate after move. \t{}".format(self._bag_details))

    @staticmethod
    def _check_path(p: str) -> bool:
        if os.path.exists(p):
            return True
        return False

    @staticmethod
    def _are_all_items_completed():
        query = (StoPDB
                 .select()
                 .where(StoPDB.completed_move == False))
        if query.exists():
            return False
        return True

    def move_items(self):
        self._items = self._mp.set_unfinished_items(self._mp.STOP)
        if len(self._items) == 0:
            self._mp.close_stop()
            return
        for i in self._items:  # type: StoPDB
            print("Working: {}".format(i.s_root))
            self._p_path_exists = False
            self._p_valid = False
            self._s_path_exists = False
            self._s_valid = False
            self._bag_details = 'No Details'

            self._current_item = i
            if not self._check_bags():
                if not self._p_path_exists:
                    # Is
                    if not self._s_path_exists:
                        # Nothing to be done find out why this path doesn't exist
                        print("Origin location does not exist: \t{}".format(self._current_item.s_root))
                        self._write_error("Origin location does not exist.")
                        continue

                    if not self._s_valid:
                        # Why is this location not valid?
                        # Maybe not bagged yet?
                        print("Attempting to bag. {}".format(self._current_item.s_root))
                        if self._try_to_bag():
                            # Okay we've bagged it. Now move it.
                            self._current_item.s_validated_on = datetime.now()
                            self._current_item.save()
                            self._prep_copy_to_destination()
                        else:
                            print("Origin location is not a valid bag: \t{}".format(self._current_item.s_root))
                            self._write_error("Origin location is not a valid bag.")
                            continue
                    else:
                        self._current_item.s_validated_on = datetime.now()
                        self._current_item.save()
                        self._prep_copy_to_destination()
            else:
                if not self._p_path_exists:
                    # Copy S to P
                    self._prep_copy_to_destination()
                # try to validate
                if self._check_bag(self._get_path_as_p(), "D"):
                    self._current_item.p_validated_on = datetime.now()
                    self._current_item.completed_move = True
                    self._current_item.save()
                else:
                    self._write_error("Destination did not validate.\t{}".format(self._bag_details))

        if self._are_all_items_completed():
            print("Completing project.  There may still be origin paths that need to be cleaned up.")
            self._mp.close_stop()

    def _write_error(self, e_text: str):
        er = Errors(sid=self._current_item,
                    error_text=e_text,
                    error_reported=datetime.now())
        er.save()


def new_file_chooser():
    mp = MoveProvider()
    op = mp.set_open_projects(mp.STOP)
    c = 1
    for i in op:  # type: ProjectID
        print("{}) {}".format(i.get_id(), i.project_file))
        c += 1
    val = input("Select a project (q to quit): ")
    if val != "q":
        mp.set_active_project(int(val))
        return True, mp
    else:
        return False, mp


if __name__ == "__main__":
    args = sys.argv

    while True:
        stp, mp = new_file_chooser()
        if stp:
            print()
            sqlmvr = SqlMover(mp)
            sqlmvr.move_items()
            print()
            print()
        else:
            break