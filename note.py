#!/usr/bin/env python3
import argparse
import re
import os
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
BASE_DIR = "$HOME/.notes"

NOTE_TEMPLATE = """\
# {year} W{week} ({week_start_date} - {week_end_date})


## Done


## TODO

{todo}

## Blockers

{blockers}

"""

SECTION_REGEX = r"(?<=## {section}\n)\s*(.*?)\s*(?=\n##|\Z)"


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


def get_year_and_week_from_date(date=None):
    if not date or date in ("this", "today"):
        date = datetime.now()
    elif date in ("last"):
        date = datetime.now() - timedelta(weeks=1)
    else:
        for fmt in FMTS:
            try:
                date = datetime.strptime(date, fmt)
                break
            except ValueError:
                continue

    if not date:
        print(f"Unable to parse date '{date}'.")
        return 1

    year = date.year
    week = date.isocalendar()[1]
    return (year, week)


def build_filename(date=None, base_dir=None):
    (year, week) = get_year_and_week_from_date(date)
    subdir = str(year)
    notes_dir = os.path.expandvars(base_dir)
    dir_path = os.path.join(notes_dir, subdir)

    start_date, end_date = iso_week_to_date_range(year, week, days=5)  # work-week only
    filename = "{}.md".format(start_date.strftime("%m-%d"))
    file_path = os.path.join(dir_path, filename)
    return file_path


def cat_section(section, date=None, base_dir=BASE_DIR):
    file_path = build_filename(date, base_dir)
    SECTION_REGEX = rf"(?<=## {section}\n)(.*?)(?=\n##|\Z)"
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r") as file:
            content = file.read()
            result = re.search(SECTION_REGEX, content, re.DOTALL)
            if result:
                output = result.group(0).strip()
                return output
    else:
        if date:
            raise FileNotFoundError(f"No notes found for date '{date}'")
        else:
            raise FileNotFoundError("No notes found for this week")


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
        help="date for which to add/open a note; always uses the beginning of the week as the filename",
        nargs="?",
    )
    parser.add_argument("--todo", action="store_true", help="print the TODO section")
    parser.add_argument(
        "--blockers", action="store_true", help="print the Blockers section"
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Base directory; defaults to $HOME/.notes",
        default=BASE_DIR,
    )

    # Parse the arguments
    args = parser.parse_args()

    if args.todo or args.blockers:
        try:
            output = cat_section(
                "TODO" if args.todo else "Blockers", args.date, args.dir
            )
            print(output)
        except Exception as e:
            print(e)
        return

    file_path = build_filename(args.date, args.dir)
    dir_path = os.path.dirname(file_path)

    os.makedirs(dir_path, exist_ok=True, mode=0o700)

    # file exists, open it
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        subprocess.call(["vim", file_path])

    # otherwise initialize it with the template
    else:
        (year, week) = get_year_and_week_from_date(args.date)
        start_date, end_date = iso_week_to_date_range(
            year, week, days=5
        )  # work-week only
        last_todo = last_blockers = None
        try:
            last_todo = cat_section("TODO", "last", args.dir)
        except Exception:
            pass
        try:
            last_blockers = cat_section("Blockers", "last", args.dir)
        except Exception:
            pass

        initial_text = NOTE_TEMPLATE.format(
            year=year,
            week=week,
            week_start_date=start_date.strftime(DATE_FMT),
            week_end_date=end_date.strftime(DATE_FMT),
            todo=f"{last_todo}\n" if last_todo else "",
            blockers=f"{last_blockers}" if last_blockers else "",
        )
        subprocess.call(["vim", "-c", "normal i{}".format(initial_text), file_path])
        subprocess.call(["bash", "-c", f"chmod 600 {file_path} 2>/dev/null || true"])


if __name__ == "__main__":
    main()
