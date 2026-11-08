#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
sdk=${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}
: "${sdk:?Android SDK dizinini ANDROID_HOME ile belirtin}"
build="$sdk/build-tools/35.0.0"
platform="$sdk/platforms/android-35/android.jar"
test -f "$platform" && test -x "$build/apksigner" || { echo 'Android platform 35 ve build-tools 35.0.0 gerekli.' >&2; exit 1; }
mkdir -p "$root/build"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/classes" "$tmp/dex"
"$build/aapt2" link -I "$platform" --manifest "$root/android/AndroidManifest.xml" -A "$root/mobile" -o "$tmp/base.apk"
javac --release 8 -classpath "$platform" -d "$tmp/classes" "$root/android/src/com/constantine/mobile/GameActivity.java"
jar cf "$tmp/app.jar" -C "$tmp/classes" .
"$build/d8" --min-api 26 --lib "$platform" --output "$tmp/dex" "$tmp/app.jar"
(cd "$tmp/dex" && zip -q -0 "$tmp/base.apk" classes.dex)
"$build/zipalign" -f 4 "$tmp/base.apk" "$tmp/aligned.apk"
# Each CI build uses a temporary test certificate.
keytool -genkeypair -keystore "$tmp/debug.jks" -storepass android -keypass android \
  -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 3650 -dname 'CN=Constantine Test'
"$build/apksigner" sign --ks "$tmp/debug.jks" --ks-pass pass:android \
  --out "$root/build/constantine-android.apk" "$tmp/aligned.apk"
"$build/apksigner" verify --verbose "$root/build/constantine-android.apk"
