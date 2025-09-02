#!/usr/bin/env python3
import argparse, sys
import pandas as pd
from numbers_parser import Document

# Fixed column names:
ROLE_COL    = "RoleName"
COMPANY_COL = "Company Name"

def load_numbers_table(path, sheet_idx=0, table_idx=0):
    doc = Document(path)
    sheet = doc.sheets[sheet_idx]
    table = sheet.tables[table_idx]
    rows = table.rows()
    data = [
        [cell.value for cell in row]
        for row in rows
        if any(cell.value is not None for cell in row)
    ]
    headers   = data[0]
    data_rows = data[1:]
    return pd.DataFrame(data_rows, columns=headers)

def main():
    p = argparse.ArgumentParser(description="Filter new offers vs Numbers master")
    p.add_argument(
        "--input", required=True,
        help="Path to the newly fetched offers CSV"
    )
    p.add_argument(
        "--numbers-file", default="Master_sheet.numbers",
        help="Path to your .numbers file"
    )
    args = p.parse_args()

    # Load data
    new_offers = pd.read_csv(args.input)
    existing   = load_numbers_table(args.numbers_file)

    # Verify required columns
    for col, src in ((ROLE_COL, "CSV"), (COMPANY_COL, "CSV")):
        if col not in new_offers.columns:
            print(f"Error: input CSV missing column {col!r}.", file=sys.stderr)
            print("Available:", list(new_offers.columns), file=sys.stderr)
            sys.exit(1)
    for col, src in ((ROLE_COL, "Numbers"), (COMPANY_COL, "Numbers")):
        if col not in existing.columns:
            print(f"Error: Numbers sheet missing column {col!r}.", file=sys.stderr)
            print("Available:", list(existing.columns), file=sys.stderr)
            sys.exit(1)

    # Identify duplicates by RoleName + Company Name
    is_dup = (
        new_offers[ROLE_COL].isin(existing[ROLE_COL])
    ) & (
        new_offers[COMPANY_COL].isin(existing[COMPANY_COL])
    )

    # Filter and write
    filtered = new_offers.loc[~is_dup]
    base, ext = args.input.rsplit(".", 1)
    out_name = f"{base}_filtered.{ext}"
    filtered.to_csv(out_name, index=False)

    print(f"Filtered out {is_dup.sum()} duplicates; {len(filtered)} remain.")
    print(f"Wrote filtered offers to {out_name!r}")

if __name__ == "__main__":
    main()
