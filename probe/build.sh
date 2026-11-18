#!/usr/bin/env bash
# Builds the probe app for the simulator into probe/build/NotificationProbe.app.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
app="$here/build/NotificationProbe.app"
rm -rf "$app" && mkdir -p "$app"
xcrun -sdk iphonesimulator swiftc -parse-as-library -target "$(uname -m)-apple-ios17.0-simulator" \
  -o "$app/NotificationProbe" "$here/main.swift"
cp "$here/Info.plist" "$app/Info.plist"
codesign --force --sign - "$app" >/dev/null
echo "$app"
