[app]

# The application name shown under the launcher icon.
title = 小星星成长记

# The package name and domain used for the Android application id.
package.name = stargrowth
package.domain = com.family

source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,otf,txt,md,json
source.exclude_dirs = tests,tools,screenshots,demo_data,demo_art,.venv,.venv313,.python313,__pycache__,.github
source.exclude_exts = spec,log,pyc

version = 1.0.0
requirements = python3,kivy==2.3.1,pillow,plyer

orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png

# Keep the diary and the photos in the app's private storage.  Android backup
# is intentionally disabled so the data is not uploaded to a cloud backup.
android.private_storage = True
android.allow_backup = False
android.permissions = VIBRATE
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.release_artifact = apk
android.debug_artifact = apk

# Do not add INTERNET to the permission list: this app never talks to a server.
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
