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
    "USB_SERIAL",
    "USB_KEYBOARDONLY",
    "USB_TOUCHSCREEN",
    "USB_HID_TOUCHSCREEN",
    "USB_HID",
    "USB_SERIAL_HID",
    "USB_MIDI",
    "USB_MIDI4",
    "USB_MIDI16",
    "USB_MIDI_SERIAL",
    "USB_MIDI4_SERIAL",
    "USB_MIDI16_SERIAL",
    "USB_AUDIO",
    "USB_MIDI_AUDIO_SERIAL",
    "USB_MIDI16_AUDIO_SERIAL",
    "USB_MTPDISK",
    "USB_RAWHID",
    "USB_FLIGHTSIM",
    "USB_FLIGHTSIM_JOYSTICK",
    "USB_EVERYTHING",
    "USB_DISABLED",
)
if not set(env.get("CPPDEFINES", [])) & set(BUILTIN_USB_FLAGS):
    env.Append(CPPDEFINES=["USB_SERIAL"])

env.Append(
    CPPDEFINES=[
        ("ARDUINO", 10805),
        ("TEENSYDUINO", int(FRAMEWORK_VERSION.split(".")[1]))
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "cores", env.BoardConfig().get("build.core"))
    ],

    LIBSOURCE_DIRS=[
        join(FRAMEWORK_DIR, "libraries")
    ]
)

if "BOARD" in env and env.BoardConfig().get("build.core") == "teensy":
    env.Append(
        ASFLAGS=["-x", "assembler-with-cpp"],

        CCFLAGS=[
            "-Os",  # optimize for size
            "-Wall",  # show warnings
            "-ffunction-sections",  # place each function in its own section
            "-fdata-sections",
            "-mmcu=$BOARD_MCU"
        ],

        CXXFLAGS=[
            "-fno-exceptions",
            "-felide-constructors",
            "-std=gnu++11"
        ],

        CPPDEFINES=[
            ("F_CPU", "$BOARD_F_CPU"),
            "LAYOUT_US_ENGLISH"
        ],

        LINKFLAGS=[
            "-Os",
            "-Wl,--gc-sections,--relax",
            "-mmcu=$BOARD_MCU"
        ],

        LIBS=["m"]
    )
elif "BOARD" in env and env.BoardConfig().get("build.core") == "teensy3":
    env.Replace(
        AR="arm-none-eabi-gcc-ar",
        RANLIB="$AR"
    )

    env.Append(
        ASFLAGS=["-x", "assembler-with-cpp"],

        CCFLAGS=[
            "-Os",  # optimize for size
            "-Wall",  # show warnings
            "-ffunction-sections",  # place each function in its own section
            "-fdata-sections",
            "-mthumb",
            "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
            "-nostdlib",
            "-fsingle-precision-constant"
        ],

        CXXFLAGS=[
            "-fno-exceptions",
            "-felide-constructors",
            "-fno-rtti",
            "-std=gnu++14",
            "-Wno-error=narrowing"
        ],

        CPPDEFINES=[
            ("F_CPU", "$BOARD_F_CPU"),
            "LAYOUT_US_ENGLISH"
        ],

        RANLIBFLAGS=["-s"],

        LINKFLAGS=[
            "-Os",
            "-Wl,--gc-sections,--relax",
            "-mthumb",
            "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
            "-Wl,--defsym=__rtc_localtime=$UNIX_TIME",
            "-fsingle-precision-constant"
        ],

        LIBS=["m", "stdc++"]
    )

    if env.BoardConfig().id_ in ("teensy35", "teensy36"):
        env.Append(
            CCFLAGS=[
                "-mfloat-abi=hard",
                "-mfpu=fpv4-sp-d16"
            ],

            LINKFLAGS=[
                "-mfloat-abi=hard",
                "-mfpu=fpv4-sp-d16"
            ]
        )

env.Append(
    ASFLAGS=env.get("CCFLAGS", [])[:]
)

if "cortex-m" in env.BoardConfig().get("build.cpu", ""):
    board = env.subst("$BOARD")
    math_lib = "arm_cortex%s_math"
    if board in ("teensy35", "teensy36"):
        math_lib = math_lib % "M4lf"
    elif board in ("teensy30", "teensy31"):
        math_lib = math_lib % "M4l"
    else:
        math_lib = math_lib % "M0l"

    env.Prepend(LIBS=[math_lib])

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
