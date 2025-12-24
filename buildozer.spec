[app]
title = G-CMCY Loadmaster
package.name = gcmcyloadmaster
package.domain = org.tecnam

source.dir = .
source.include_exts = py,png,jpg,kv

version = 1.0

requirements = python3,kivy,matplotlib,fpdf2,kiwisolver,cycler,pyparsing,python-dateutil

garden_requirements = matplotlib

orientation = portrait
fullscreen = 0

icon.filename = static/logo.jpg

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
