[app]
title = NeoTorrent
package.name = neotorrent
package.domain = org.neo
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# THE ENGINE
# We remove 'openssl' here to avoid the conflict that killed Colab
requirements = python3,kivy,android,requests,openssl

# PERMISSIONS (Ironclad)
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,WAKE_LOCK,FOREGROUND_SERVICE

# SCREEN
orientation = portrait
fullscreen = 0

# ANDROID VERSION
android.archs = arm64-v8a
android.allow_backup = True
android.api = 31
android.minapi = 21

[buildozer]
log_level = 2
warn_on_root = 0
