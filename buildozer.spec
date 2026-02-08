[app]

# (section) Title of your application
title = NeoOnyx

# (section) Package name
package.name = neoonyx

# (section) Package domain (needed for android package name)
package.domain = org.neomind

# (section) Source code where the main.py live
source.dir = .

# (section) Application version
version = 2.0

# (section) Application requirements
# Essential for the Fusion features including the Torrent Engine and AI API
requirements = python3, kivy, libtorrent, openssl, requests, certifi, chardet, idna, urllib3

# (section) Supported orientations
orientation = portrait

# (section) Android specific
# Required for downloading to your high-capacity storage
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

# (section) API level (33 is Android 13, 34 is Android 14)
android.api = 34

# (section) Minimum API level
android.minapi = 21

# (section) Architecture
# Optimized for your Snapdragon 8s Gen 4
android.archs = arm64-v8a

# (section) Intent Filters
# Allows the "Magnet Link Interception" feature to work automatically
android.manifest.intent_filters = [
    {"action": "android.intent.action.VIEW", 
     "categories": ["android.intent.category.DEFAULT", "android.intent.category.BROWSABLE"], 
     "data": {"scheme": "magnet"}}
]

# (section) Buildozer settings
[buildozer]
log_level = 2
warn_on_root = 1
