[app]
title = NeoOnyx Fusion
package.name = neoonyx
package.domain = org.ikred
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# REQUIREMENTS: hostpython3 is mandatory for libtorrent C++ linking
requirements = python3, kivy==2.3.0, libtorrent, openssl, requests, certifi, chardet, idna, urllib3, hostpython3

# CRITICAL: Switch to develop branch for latest recipe patches
p4a.branch = develop

# ANDROID CONFIGURATION (Targeting API 34 for Play Store standards)
android.api = 34
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a

# PERMISSIONS & BROWSER INTERCEPT
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE
android.manifest.intent_filters = [ \
    {"action": "android.intent.action.VIEW", \
     "category": ["android.intent.category.DEFAULT", "android.intent.category.BROWSABLE"], \
     "data": {"scheme": "magnet"}}]

fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
