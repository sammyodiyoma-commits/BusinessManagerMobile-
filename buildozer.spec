[app]
title = Business Manager
package.name = businessmanager
package.domain = com.sammy

source.dir = .
source.include_exts = py,db,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy==2.3.1

orientation = portrait
fullscreen = 0

android.archs = arm64-v8a,armeabi-v7a
android.api = 33
android.minapi = 24

android.allow_backup = True
android.debug_artifact = apk

p4a.branch = master

[buildozer]

log_level = 2
warn_on_root = 1
""")'
