# rename_to_osis.ps1
# Renames non-OSIS book codes to OSIS-compliant codes
# Preserves full filename structure:
# NNN_BOOK_CCC_VVV_VERSION.txt

# Mapping table
$map = @{
    "1JO" = "1JN"
    "2JO" = "2JN"
    "3JO" = "3JN"
    "EZE" = "EZK"
    "NAH" = "NAM"
    "PLM" = "PHM"
}

# Get all .txt files recursively from current directory
Get-ChildItem -Recurse -Filter *.txt | ForEach-Object {

    $name = $_.Name

    # Expected format: NNN_BOOK_CCC_VVV_VERSION.txt
    if ($name -match '^(\d{3})_([A-Z0-9]+)_(\d{3})_(\d{3})_([A-Z0-9]+)\.txt$') {

        $conical = $matches[1]
        $book    = $matches[2]
        $chapter = $matches[3]
        $verse   = $matches[4]
        $version = $matches[5]

        if ($map.ContainsKey($book)) {

            $newBook = $map[$book]

            $newName = "{0}_{1}_{2}_{3}_{4}.txt" -f `
                $conical, $newBook, $chapter, $verse, $version

            $newPath = Join-Path $_.DirectoryName $newName

            Rename-Item $_.FullName $newPath

            Write-Host "Renamed: $name -> $newName"
        }
    }
}
