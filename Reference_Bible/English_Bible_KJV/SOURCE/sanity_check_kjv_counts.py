import os
import re
import sys
from collections import defaultdict

ROOT = "atoms/KJV"

# Canonical expected verse counts (Protestant 66-book canon)
EXPECTED = {
    "GEN": 1533, "EXO": 1213, "LEV": 859,  "NUM": 1288, "DEU": 959,
    "JOS": 658,  "JDG": 618,  "RUT": 85,   "1SA": 810,  "2SA": 695,
    "1KI": 816,  "2KI": 719,  "1CH": 942,  "2CH": 822, "EZR": 280,
    "NEH": 406,  "EST": 167,  "JOB": 1070, "PSA": 2461,"PRO": 915,
    "ECC": 222,  "SNG": 117,  "ISA": 1292, "JER": 1364,"LAM": 154,
    "EZE": 1273, "DAN": 357,  "HOS": 197,  "JOL": 73,  "AMO": 146,
    "OBA": 21,   "JON": 48,   "MIC": 105,  "NAH": 47, "HAB": 56,
    "ZEP": 53,   "HAG": 38,   "ZEC": 211,  "MAL": 55,
    "MAT": 1071, "MRK": 678,  "LUK": 1151, "JHN": 879, "ACT": 1007,
    "ROM": 433,  "1CO": 437,  "2CO": 257,  "GAL": 149, "EPH": 155,
    "PHP": 104,  "COL": 95,   "1TH": 89,   "2TH": 47, "1TI": 113,
    "2TI": 83,   "TIT": 46,   "PLM": 25,   "HEB": 303, "JAS": 108,
    "1PE": 105,  "2PE": 61,   "1JN": 105,  "2JN": 13, "3JN": 14,
    "JUD": 25,   "REV": 404,
}

FILENAME_RE = re.compile(r'^\d{3}_([A-Z0-9]{3})_\d{3}_\d{3}_KJV\.txt$')

counts = defaultdict(int)

# Walk all files (flattened or per-book dirs both work)
for root, _, files in os.walk(ROOT):
    for f in files:
        m = FILENAME_RE.match(f)
        if not m:
            print("BAD FILENAME:", f)
            sys.exit(1)
        book_id = m.group(1)
        counts[book_id] += 1

# Report + verify
print("KJV VERSE COUNT CHECK")
print("======================")

total = 0
errors = False

for book_id, expected in EXPECTED.items():
    found = counts.get(book_id, 0)
    total += found
    status = "OK"
    if found != expected:
        status = "FAIL"
        errors = True
    print(f"{book_id:>3}: {found:4d} / {expected:4d}  {status}")

print("----------------------")
print("TOTAL:", total, "/ 31101")

if total != 31101:
    print("FAIL: total verse count mismatch")
    errors = True

if errors:
    print("\nSANITY CHECK FAILED")
    sys.exit(1)
else:
    print("\nSANITY CHECK PASSED")