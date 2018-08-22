from bulk_mover.move_db import db_reports
from bulk_mover.mover import Coordinator


def generate_index():
    db_reports.stop_index_report()


def move_s_to_p():
    coord = Coordinator()
    coord.menu()


def main():
    main_menu = """
        1) Generate an Index.
        2) Do move from S to P
        3) Quit
    """

    print(main_menu)

    val = input("What do you want to do? ")
    if int(val) == 1:
        generate_index()
        main()

    if int(val) == 2:
        move_s_to_p()
        main()

    if int(val) == 3:
        exit(0)


if __name__ == '__main__':
    main()