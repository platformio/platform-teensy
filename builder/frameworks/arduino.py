# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Arduino

Arduino Wiring-based Framework allows writing cross-platform software to
control devices attached to a wide range of Arduino boards to create all
kinds of creative coding, interactive objects, spaces or physical experiences.

http://arduino.cc/en/Reference/HomePage
"""

from os import listdir
from os.path import isdir, isfile, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()

FRAMEWORK_DIR = platform.get_package_dir("framework-arduinoteensy")
FRAMEWORK_VERSION = platform.get_package_version("framework-arduinoteensy")
assert isdir(FRAMEWORK_DIR)

BUILTIN_USB_FLAGS = (
    "USB_AUDIO",
    "USB_HID",
    "USB_SERIAL_HID",
    "USB_DISK",
    "USB_DISK_SDFLASH",
    "USB_MIDI",
    "USB_RAWHID",
    "USB_FLIGHTSIM",
    "USB_DISABLED"
)
if not set(env.get("CPPDEFINES", [])) & set(BUILTIN_USB_FLAGS):
    env.Append(CPPDEFINES=["USB_SERIAL"])

env.Append(
    CPPDEFINES=[
        ("ARDUINO", 10610),
        ("TEENSYDUINO", FRAMEWORK_VERSION.split(".")[1])
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "cores", env.BoardConfig().get("build.core"))
    ],

    LIBSOURCE_DIRS=[
        join(FRAMEWORK_DIR, "libraries")
    ]
)

# Teensy 2.x Core
if env.BoardConfig().get("build.core") == "teensy":
    env.Append(CPPPATH=[join(FRAMEWORK_DIR, "cores")])

    # search relative includes in teensy directories
    core_dir = join(FRAMEWORK_DIR, "cores", "teensy")
    for item in sorted(listdir(core_dir)):
        file_path = join(core_dir, item)
        if not isfile(file_path):
            continue
        content = None
        content_changed = False
        with open(file_path) as fp:
            content = fp.read()
            if '#include "../' in content:
                content_changed = True
                content = content.replace('#include "../', '#include "')
        if not content_changed:
            continue
        with open(file_path, "w") as fp:
            fp.write(content)
else:
    env.Prepend(LIBPATH=[join(FRAMEWORK_DIR, "cores", "teensy3")])

#
# Target: Build Core Library
#

libs = []

if "build.variant" in env.BoardConfig():
    env.Append(
        CPPPATH=[
            join(FRAMEWORK_DIR, "variants",
                 env.BoardConfig().get("build.variant"))
        ]
    )
    libs.append(env.BuildLibrary(
        join("$BUILD_DIR", "FrameworkArduinoVariant"),
        join(FRAMEWORK_DIR, "variants", env.BoardConfig().get("build.variant"))
    ))

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "FrameworkArduino"),
    join(FRAMEWORK_DIR, "cores", env.BoardConfig().get("build.core"))
))

env.Prepend(LIBS=libs)
