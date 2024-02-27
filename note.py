#!/usr/bin/env python3
import os
import argparse
import subprocess
from datetime import datetime, timedelta

FMTS = [
    # 4-digit year
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    # 2-digit year, year needs to come first
    "%y-%m-%d",
    "%y/%m/%d",
]
DATE_FMT = "%Y/%m/%d"

NOTE_TEMPLATE = """\
# {year} W{week} ({week_start_date} - {week_end_date})


## Done


## TODO


## Blockers


"""


def iso_week_to_date_range(year, week, days=7):
    # January 4th is always in the first week of the given year.
    # (ISO weeks start on Monday)
    jan4 = datetime(year, 1, 4)

    # Find the Monday of the first week of the year
    start_of_year_week = jan4 - timedelta(days=jan4.isoweekday() - 1)

    # Calculate the start date of the given week number
    start_date = start_of_year_week + timedelta(weeks=week - 1)

    # The end date is 6 days after the start date since ISO weeks are 7 days long
    end_date = start_date + timedelta(days=days - 1)  # work-week only

    return start_date, end_date


def main():
    parser = argparse.ArgumentParser(
        description="""\
Notes.

Create weekly markdown notes in '$HOME/.notes', organized as `YYYY/MM-DD.md`.

Pass a YYYY-MM-DD date to open a note for the week corresponding to that date;
Omit or use 'this' to either create or open an existing note for this week;
Use 'last' to to create or open an existing note for last week.
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Add arguments
    parser.add_argument(
        "date",
        type=str,
        help="Date for which to create/open a note; always uses the beginning of the week as the filename",
        nargs="?",
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Base directory; defaults to $HOME/.notes",
        default="$HOME/.notes",
    )

    # Parse the arguments
    args = parser.parse_args()

    date = None
    if not args.date or args.date in ("this", "today"):
        date = datetime.now()
    elif args.date in ("last"):
        date = datetime.now() - timedelta(weeks=1)
    else:
        for fmt in FMTS:
            try:
                date = datetime.strptime(args.date, fmt)
                break
            except ValueError:
                continue

    if not date:
        print(f"Unable to parse date '{args.date}'.")
        return 1

    subdir = date.strftime("%Y")
    notes_dir = os.path.expandvars(args.dir)
    dir_path = os.path.join(notes_dir, subdir)

    year = date.year
    week = date.isocalendar()[1]
    start_date, end_date = iso_week_to_date_range(year, week, days=5)  # work-week only
    filename = "{}.md".format(start_date.strftime("%m-%d"))
    file_path = os.path.join(dir_path, filename)

    os.makedirs(dir_path, exist_ok=True, mode=0o700)

    # file exists, open it
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        subprocess.call(["vim", file_path])

    # otherwise initialize it with the template
    else:
        initial_text = NOTE_TEMPLATE.format(
            year=year,
            week=week,
            week_start_date=start_date.strftime(DATE_FMT),
            week_end_date=end_date.strftime(DATE_FMT),
        )
        subprocess.call(["vim", "-c", "normal i{}".format(initial_text), file_path])
        subprocess.call(["bash", "-c", f"chmod 600 {file_path} 2>/dev/null || true"])


if __name__ == "__main__":
    main()
