@echo off
echo === Renaming WEBUS Romans doxology to KJV/TR numbering ===

REM Safety check
if not exist 045_ROM_014_024_WEBUS.txt (
    echo ERROR: 045_ROM_014_024_WEBUS.txt not found
    goto :eof
)

if not exist 045_ROM_014_025_WEBUS.txt (
    echo ERROR: 045_ROM_014_025_WEBUS.txt not found
    goto :eof
)

if not exist 045_ROM_014_026_WEBUS.txt (
    echo ERROR: 045_ROM_014_026_WEBUS.txt not found
    goto :eof
)

REM Rename in reverse order to avoid collisions

rename 045_ROM_014_026_WEBUS.txt 045_ROM_016_027_WEBUS.txt
rename 045_ROM_014_025_WEBUS.txt 045_ROM_016_026_WEBUS.txt
rename 045_ROM_014_024_WEBUS.txt 045_ROM_016_025_WEBUS.txt

echo === Rename complete ===
