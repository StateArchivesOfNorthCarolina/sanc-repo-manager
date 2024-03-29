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

    try:
        val = int(val)
    except ValueError as e:
        print("\n\n### Selection must be a positive integer ###")
        main()

    if int(val) == 1:
        generate_index() #Creates a spreadsheet of the S and corresponding P locations. It calls the database and prints the root path for the s drive and the p drive.
        main()

    if int(val) == 2:
        move_s_to_p() #Opens the main menu for program. Aims at mover.py
        main()

    if int(val) == 3: #Exits the program
        exit(0)


if __name__ == '__main__':
    main()