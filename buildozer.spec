[app]
title = Contacts Personnels Premium
package.name = contactspremium
package.domain = fr.personnel
source.dir = .
source.include_exts = py,png,jpg,kv,json,atlas,md
version = 1.0.0
requirements = python3,kivy,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = CALL_PHONE
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
