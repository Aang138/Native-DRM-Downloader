#!/bin/bash
set -e

APP_GRADLE="app/build.gradle"

if [ ! -f "$APP_GRADLE" ]; then
  echo "ERROR: app/build.gradle not found. Run this from your repo root."
  exit 1
fi

if grep -q "youtubedl-android" "$APP_GRADLE"; then
  echo "Dependencies already present, skipping."
else
  python3 - << 'PYEOF'
import re

with open("app/build.gradle", "r") as f:
    content = f.read()

new_deps = '''    implementation 'io.github.junkfood02.youtubedl-android:library:0.18.1'
    implementation 'io.github.junkfood02.youtubedl-android:ffmpeg:0.18.1'
    implementation 'io.github.junkfood02.youtubedl-android:aria2c:0.18.1'
'''

pattern = re.compile(r'(dependencies\s*\{)')
content_new, count = pattern.subn(r'\1\n' + new_deps, content, count=1)

if count == 0:
    print("WARNING: no 'dependencies {' block found in app/build.gradle.")
    print(new_deps)
else:
    with open("app/build.gradle", "w") as f:
        f.write(content_new)
    print("Dependencies added to app/build.gradle")
PYEOF
fi

echo ""
echo "Checking settings.gradle..."
if [ -f "settings.gradle" ]; then
  if grep -q "mavenCentral()" settings.gradle; then
    echo "mavenCentral() configured successfully."
  else
    echo "WARNING: mavenCentral() not found in settings.gradle."
  fi
else
  echo "settings.gradle not found."
fi

echo ""
echo "Done. Review changes with: git diff app/build.gradle"
