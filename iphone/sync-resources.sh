#!/usr/bin/env bash
# Copy bundled editions + Literata font into the app resources (same set as the Android build).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$here/.."
res="$here/Sources/GOIBible/Resources"
mkdir -p "$res"
for db in GOI_En.db GOI_Zh_Hant.db GOI_Zh_Hans.db GOI_vi.db; do
    cp "$root/Meta_Bible_Data/goi_db_download/$db" "$res/"
done
cp "$root/Apps/GOIBible_android/app/src/main/res/font/literata.ttf" "$res/Literata.ttf"
# Asset catalog icon for Xcode (CI) builds: iOS single-size + macOS size set. xtool uses Resources/AppIcon.png.
icon="$here/Resources/Assets.xcassets/AppIcon.appiconset"
mkdir -p "$icon"
cp "$here/Resources/AppIcon.png" "$icon/AppIcon.png"
images='{"filename":"AppIcon.png","idiom":"universal","platform":"ios","size":"1024x1024"}'
for s in 16 32 128 256 512; do
    for scale in 1 2; do
        px=$((s * scale)); f="mac_${s}@${scale}x.png"
        if [ ! -f "$icon/$f" ]; then
            if command -v convert >/dev/null; then convert "$here/Resources/AppIcon.png" -resize "${px}x${px}" "$icon/$f"
            else sips -z "$px" "$px" "$here/Resources/AppIcon.png" --out "$icon/$f" >/dev/null; fi  # macOS
        fi
        images="$images,{\"filename\":\"$f\",\"idiom\":\"mac\",\"scale\":\"${scale}x\",\"size\":\"${s}x${s}\"}"
    done
done
echo "{\"images\":[$images],\"info\":{\"author\":\"xcode\",\"version\":1}}" > "$icon/Contents.json"
echo '{"info":{"author":"xcode","version":1}}' > "$here/Resources/Assets.xcassets/Contents.json"
ls -la "$res"
