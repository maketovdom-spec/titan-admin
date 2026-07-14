[app]
title = TITAN Admin
package.name = titanadmin
package.domain = org.titan.admin

source.main = admin.py
source.include_exts = py,png,jpg,kv,atlas,json

version = 0.1

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
