[app]

# (str) Title of your application
title = NeoOnyx Fusion

# (str) Package name
package.name = neoonyx

# (str) Package domain (needed for android packaging)
package.domain = org.ikred

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let's keep it lean)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning
version = 1.0.0

# REQUIREMENTS: 
# Using python3==3.11 is mandatory for the libtorrent C++ engine.
# hostpython3 is required for cross-compiling the native recipes.
requirements = python3==3.11, kivy==2.3.0, libtorrent, openssl, requests, certifi, chardet, idna, urllib3, hostpython3

# THE CRITICAL FIX: Use the master branch for 2026 C++ compatibility patches
p4a.branch = master

# (str) Supported orientations
orientation = portrait

# (bool) Fullscreen mode
fullscreen = 1

# --- ANDROID SETTINGS ---

# (int) Target Android API (API 34 is the 2026 standard for Store readiness)
android.api = 34

# (int) Minimum API supported (Android 5.0+)
android.minapi = 21

# (str) Android NDK version (r25b is the 'Gold Standard' for libtorrent stability)
android.ndk = 25b

# (int) Android NDK API to use
android.ndk_api = 21

# (list) The Android architectures to build for.
# arm64-v8a is essential for the performance of your iQOO Neo 10.
android.archs = arm64-v8a

# (list) Permissions required for a 99% better torrent experience
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE

# (list) INTENT FILTERS: This makes NeoOnyx open automatically when clicking magnet links
android.manifest.intent_filters = [ \
    {"action": "android.intent.action.VIEW", \
     "category": ["android.intent.category.DEFAULT", "android.intent.category.BROWSABLE"], \
     "data": {"scheme": "magnet"}}]

# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# --- APP ICONS AND SPLASH (Optional defaults) ---
# android.presplash_color = #080808
# android.icon.adaptive_foreground.filename = %(source.dir)s/icon.png

[buildozer]

# (int) Log level (2 = debug info for troubleshooting)
log_level = 2

# (int) Display warning if buildozer is run as root (1 = enabled)
warn_on_root = 1
