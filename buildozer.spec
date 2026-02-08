[app]
title = NeoOnyx Fusion
package.name = neoonyx
package.domain = org.ikred
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# REQUIREMENTS: Hostpython3 is vital for compiling libtorrent
requirements = python3, kivy==2.3.0, libtorrent, openssl, requests, certifi, chardet, idna, urllib3, hostpython3

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a

# ANDROID SETTINGS
android.api = 34
android.minapi = 21
android.ndk = 26b
android.accept_sdk_license = True

# INTENT FILTERS (For Browser Intercept)
android.manifest.intent_filters = [ \
    {"action": "android.intent.action.VIEW", \
     "category": ["android.intent.category.DEFAULT", "android.intent.category.BROWSABLE"], \
     "data": {"scheme": "magnet"}}]

[buildozer]
log_level = 2
warn_on_root = 1
