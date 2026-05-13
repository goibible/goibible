import os

ROOT = "atoms/KJV"

suspects = []

for root, _, files in os.walk(ROOT):
    for f in files:
        path = os.path.join(root, f)
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read().strip()
            # Psalm titles usually start with "A Psalm", "To the chief Musician", etc.
            if text.startswith(("A Psalm", "To the chief", "Maschil", "Michtam")):
                suspects.append((f, text))

for f, text in suspects:
    print(f)
    print("  ", text)