import os
from playhouse.migrate import *
from peewee import *
from pathlib import Path

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
dir_path = os.path.join(dir_path, 'db')

# If you are using this from the USB stick DO CHANGE THIS
db_name = os.path.join(dir_path, 'StoPMove.db')

db = SqliteDatabase(db_name, pragmas=(('foreign_keys', 'on'),))


class BaseModel(Model):
    class Meta:
        database = db
        only_save_dirty = True


class ProjectID(BaseModel):
    project_file = TextField(unique=True)
    project_added = DateTimeField()
    stop_complete = BooleanField(default=False)
    ptoa_complete = BooleanField(default=False)
    project_completed = BooleanField(default=False)


class StoPDB(BaseModel):
    pid = ForeignKeyField(ProjectID)
    s_root = TextField(unique=True)
    p_root = TextField(unique=False)
    s_validated_on = DateTimeField(null=True)
    p_validated_on = DateTimeField(null=True)
    s_removed_on = DateTimeField(null=True)
    completed_move = BooleanField(default=False)
    is_bagged = BooleanField(default=False)
    a_complete = BooleanField(default=False)
    skip = BooleanField(default=False)
    has_notes = BooleanField(default=False)


class OrigPathDups(BaseModel):
    sid = ForeignKeyField(StoPDB)
    attempted_project = ForeignKeyField(ProjectID)
    attempted_line = TextField(unique=False)
    seen_before = CharField(unique=True)


class StoPparts(BaseModel):
    root = ForeignKeyField(StoPDB)
    lvl1 = TextField()
    lvl2 = TextField()
    lvl3 = TextField()
    lvl4 = TextField(null=True)
    lvl5 = TextField(null=True)
    lvl6 = TextField(null=True)


class Errors(BaseModel):
    sid = ForeignKeyField(StoPDB)
    error_text = TextField()
    error_reported = DateTimeField()


class FakeAccessions(BaseModel):
    root = ForeignKeyField(StoPDB)
    fa_type = CharField(default='F')
    fa_num = IntegerField(null=True)


class VerifiedPaths(BaseModel):
    part_id = ForeignKeyField(StoPparts)
    path = TextField()
    valid = BooleanField(default=False)


class Notes(BaseModel):
    sid = ForeignKeyField(StoPparts)
    note = TextField()


class PtoADB(BaseModel):
    fk = ForeignKeyField(StoPDB, unique=True)
    completed_conversion = BooleanField(default=False)
    date_completed = DateTimeField(null=True)


class PtoAFiles(BaseModel):
    fk = ForeignKeyField(PtoADB, index=True)
    p_file_name = TextField(unique=True)
    p_file_size = BigIntegerField(null=True)
    a_file_name = TextField(null=True)
    a_file_size = BigIntegerField(null=True)
    completed = BooleanField(default=False)
    date_completed = DateTimeField(null=True)


class PtoAError(BaseModel):
    fk = ForeignKeyField(PtoAFiles)
    error_msg = TextField(null=True)


class Cleanup(BaseModel):
    fk = ForeignKeyField(StoPDB)



db.connect()


def create_tables():
    l = [PtoADB, PtoAFiles, PtoAError, ProjectID, StoPDB, StoPparts, FakeAccessions, Errors, OrigPathDups,
         VerifiedPaths, Notes]
    for t in l:
        try:
            db.create_tables(t)
        except OperationalError as e:
            pass


#create_tables()


def test():
    query = (PtoAFiles.select().where(PtoAFiles.fk == 3 & PtoAFiles.completed is False))
    if query.exists():
        print(query.count())
    else:
        print()


if __name__ == '__main__':
    """
    my_db = SqliteDatabase(db_name)
    migrator = SqliteMigrator(my_db)
    

    migrate(
        migrator.add_column('fakeaccessions', 'fa_type', fa_type),
        migrator.add_column('fakeaccessions', 'fa_num', fa_num),
    )
    """






