[app]
# (str) Title of your application
title = NeoOnyx Fusion

# (str) Package name
package.name = neoonyx

# (str) Package domain (needed for android packaging)
package.domain = org.ikred

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas

# (str) Application version
version = 1.0.0

# (list) Application requirements
# hostpython3 and Cython pinning are handled in the build.yml
requirements = python3, kivy==2.3.0, libtorrent, openssl, requests, certifi, chardet, idna, urllib3, hostpython3

# (str) Custom source folders for requirements
# p4a.branch = master is the "magic fix" for 2026 libtorrent builds
p4a.branch = master

# (int) Android API to use
android.api = 34
android.minapi = 21

# (str) Android NDK version to use
# r25b is the current 'stability king' for arm64-v8a
android.ndk = 25b
android.ndk_api = 21

# (list) The Android architectures to build for
# Optimized for your iQOO Neo 10 performance
android.archs = arm64-v8a

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE

# (list) Intent filters for Browser Magnet Intercept
android.manifest.intent_filters = [ \
    {"action": "android.intent.action.VIEW", \
     "category": ["android.intent.category.DEFAULT", "android.intent.category.BROWSABLE"], \
     "data": {"scheme": "magnet"}}]

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

[buildozer]
# (int) Log level (2 = debug)
log_level = 2
warn_on_root = 1
