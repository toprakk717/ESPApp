[app]
title = ESP
package.name = esp
package.domain = com.axiom
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3,kivy,opencv,numpy
android.permissions = CAMERA,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a

[buildozer]
log_level = 2
