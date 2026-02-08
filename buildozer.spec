[app]
title = NeoOnyx Fusion
package.name = neoonyx
package.domain = org.ikred
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# Pinning to Python 3.11 for C++ stability
requirements = python3==3.11, kivy==2.3.0, libtorrent, openssl, requests, certifi, chardet, idna, urllib3, hostpython3

p4a.branch = master
orientation = portrait
fullscreen = 1

# Android Settings
android.api = 34
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE
android.manifest.intent_filters = [ \
    {"action": "android.intent.action.VIEW", \
     "category": ["android.intent.category.DEFAULT", "android.intent.category.BROWSABLE"], \
     "data": {"scheme": "magnet"}}]

[buildozer]
log_level = 2
warn_on_root = 1
