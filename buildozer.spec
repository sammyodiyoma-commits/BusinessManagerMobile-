[app]
title = Business Manager
package.name = businessmanager
package.domain = com.sammy
source.dir = .
source.include_exts = py,kv,db,png,jpg,jpeg,atlas
version = 1.0
requirements = python3,kivy==2.3.1
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0

[android]
android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.enable_androidx = True
