[app]
title = ESP
package.name = esp
package.domain = com.axiom

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,prototxt,caffemodel

version = 1.0

requirements = python3,kivy,numpy,opencv,pyjnius

android.api = 33
android.minapi = 24
android.archs = arm64-v8a

android.permissions = CAMERA,FOREGROUND_SERVICE,SYSTEM_ALERT_WINDOW

orientation = portrait

fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
