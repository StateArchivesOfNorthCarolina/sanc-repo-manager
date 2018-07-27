from pathlib import Path
from move_db.MoverDBs import *
from mover_classes.SANCBagger import SANCBagger
from datetime import datetime
import sys
from shutil import rmtree
from hashlib import md5
import re

class SqlCleanup:

    def __init__(self, p: ProjectID) -> None:
        self.prj = p  # type: ProjectID
        self.stopdbs = []  # type: [StoPDB]

    def check_stopdbs(self):
        query = (StoPDB
                 .select()
                 .where((StoPDB.pid == self.prj) & (StoPDB.s_removed_on.is_null()) & (StoPDB.has_notes == False))
                 )
        results = False

        for stop in query:  # type: StoPDB
            results = True
            s = Path(stop.s_root)
            d = Path("P:\\", stop.p_root)
            print("Checking:\t{}".format(stop.s_root))
            if s.exists():
                # Validate P:
                if not d.exists():
                    # P is not really there. Report and stop
                    print("P path does not exist:\t{}".format(stop.p_root))
                    continue
                else:
                    # Validate P
                    sb = SANCBagger()
                    sb.open_bag(str(d))
                    if sb.quick_validate():
                        # Validated. Remove S:
                        # check to see that S is equivalent to p
                        if not self._check_for_equiv(s, d):
                            print("Source bag not equivalent to dest bag: \t{}\t{}".format(stop.s_root, stop.p_root))
                            val = input("Continue removing the source (y/n): ")
                            if val == 'n':
                                continue
                        print("Closing:\t{}".format(stop.s_root))
                        stop.p_validated_on = datetime.now()
                        stop.s_validated_on = datetime.now()
                        try:
                            rmtree(str(s))
                        except PermissionError as e:
                            print("Could not be removed automatically:\t {}".format(s))
                            print("Remove manually and update db.")
                            val = input("Hit any key to continue?: ")
                        stop.s_removed_on = datetime.now()
                        stop.save()
                    else:
                        print("Not Valid:\t{}\t{}\t{}".format(sb.bagging_error, sb.validation_error_details, sb.validation_error_message))
                        continue
            else:
                # S is already gone so this better validate
                if d.exists():
                    sb = SANCBagger()
                    if not sb.open_bag(str(d)):
                        print("Unable to open bag at:\t{}".format(d))
                        continue
                    if sb.quick_validate():
                        # Validated
                        print("Closing:\t{}".format(stop.s_root))
                        stop.p_validated_on = datetime.now()
                        stop.s_validated_on = datetime.now()
                        stop.s_removed_on = datetime.now()
                        stop.save()
                    else:
                        print("Destination is not validating:\t{}".format(d))

        q = (StoPDB
                 .select()
                 .where((StoPDB.pid == self.prj) & (StoPDB.s_removed_on.is_null()) & (StoPDB.has_notes == False))
                 )

        if not q.exists():
            self.prj.project_completed = True
            self.prj.save()


    def _check_for_equiv(self, s: Path, d: Path):
        sm = s / self._get_manifest_at_location(s)  # type: Path
        dm = d / self._get_manifest_at_location(d)  # type: Path
        h1 = md5()
        h2 = md5()
        h1.update(sm.read_bytes())
        h2.update(dm.read_bytes())
        if h1.hexdigest() == h2.hexdigest():
            return True
        else:
            return False

    def _get_manifest_at_location(self, p: Path) -> str:
        # if neither of these are in place at location then this will fail
        for f in p.iterdir():
            if re.match("^manifest-.*", str(f.name)):
                return str(f.name)



def project_select() -> ProjectID:
    prjs = []
    project = (ProjectID
               .select()
               .where((ProjectID.project_completed == False))
               )
    for prj in project:  # type: ProjectID
        print("{})\t{}".format(prj.id, prj.project_file))
        prjs.append(prj)

    val = input("Which project do you want to cleanup? ")
    pro = ProjectID.get(ProjectID.id == int(val))
    return pro


if __name__ == '__main__':
    sqlc = SqlCleanup(project_select())
    sqlc.check_stopdbs()