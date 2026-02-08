[app]
title = NeoOnyx Fusion
package.name = neoonyx
package.domain = org.ikred
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# CHANGE: Using libtorrent-python instead of the legacy libtorrent recipe
# Also adding 'hostpython3' as it is a mandatory build requirement
requirements = python3, kivy==2.3.0, libtorrent-python, openssl, requests, certifi, chardet, idna, urllib3, hostpython3

# CRITICAL: Stay on the 'develop' branch for the newer recipe
p4a.branch = develop

android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# ... (keep your existing permissions and intent filters)
