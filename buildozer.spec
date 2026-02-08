[app]
title = NeoOnyx Fusion
package.name = neoonyx
package.domain = org.ikred
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# REQUIREMENTS: Switched to 'libtorrent-python' for Python 3.11 compatibility
requirements = python3, kivy==2.3.0, libtorrent-python, openssl, requests, certifi, chardet, idna, urllib3, hostpython3

# CRITICAL: Use develop branch for the latest recipe patches
p4a.branch = develop

# ANDROID CONFIGURATION
android.api = 34
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a

# PERMISSIONS
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE

# BROWSER INTERCEPT (Magnet Link Handling)
android.manifest.intent_filters = [ \
    {"action": "android.intent.action.VIEW", \
     "category": ["android.intent.category.DEFAULT", "android.intent.category.BROWSABLE"], \
     "data": {"scheme": "magnet"}}]

fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
