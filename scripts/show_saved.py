"""Read persisted entries for the demo, without adding a fourth MCP tool."""

import argparse
import json
import sqlite3
from pathlib import Path

from campus_mcp.service import DEFAULT_DB


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    if not args.db.is_file():
        parser.exit(1, "No reading-list database yet. Save a book first.\n")
    try:
        with sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM reading_list ORDER BY list_name, book_id").fetchall()
        print(json.dumps([dict(row) for row in rows], indent=2))
    except sqlite3.Error:
        parser.exit(1, "Could not read the reading-list database.\n")


if __name__ == "__main__":
    main()
