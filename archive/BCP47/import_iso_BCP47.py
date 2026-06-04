import sqlite3

conn = sqlite3.connect("bcp47.sqlite3")
cur = conn.cursor()

with open("language-subtag-registry", "r", encoding="utf-8") as f:
    content = f.read()

blocks = content.split("%%")

for block in blocks:
    lines = block.strip().splitlines()
    data = {}
    for line in lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            data.setdefault(key, []).append(value)

    type_ = data.get("Type", [None])[0]
    subtag = data.get("Subtag", [None])[0]
    desc = data.get("Description", [""])[0]
    deprecated = 1 if "Deprecated" in data else 0
    preferred = data.get("Preferred-Value", [None])[0]
    suppress = data.get("Suppress-Script", [None])[0]

    if type_ == "language":
        cur.execute("""
            INSERT OR IGNORE INTO iso_languages
            (subtag, description, suppress_script, deprecated, preferred_value)
            VALUES (?, ?, ?, ?, ?)
        """, (subtag, desc, suppress, deprecated, preferred))

    elif type_ == "script":
        cur.execute("""
            INSERT OR IGNORE INTO iso_scripts
            (subtag, description, deprecated, preferred_value)
            VALUES (?, ?, ?, ?)
        """, (subtag, desc, deprecated, preferred))

    elif type_ == "region":
        cur.execute("""
            INSERT OR IGNORE INTO iso_regions
            (subtag, description, deprecated, preferred_value)
            VALUES (?, ?, ?, ?)
        """, (subtag, desc, deprecated, preferred))

conn.commit()
conn.close()