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

from io import open
from os import listdir
from os.path import isdir, isfile, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()

FRAMEWORK_DIR = platform.get_package_dir("framework-arduinoteensy")
FRAMEWORK_VERSION = platform.get_package_version("framework-arduinoteensy")
BUILD_CORE = env.BoardConfig().get("build.core")

assert isdir(FRAMEWORK_DIR)

BUILTIN_USB_FLAGS = (
    "USB_SERIAL",
    "USB_DUAL_SERIAL",
    "USB_TRIPLE_SERIAL",
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
    "USB_MTPDISK_SERIAL"
)
if not set(env.get("CPPDEFINES", [])) & set(BUILTIN_USB_FLAGS):
    env.Append(CPPDEFINES=["USB_SERIAL"])

env.Replace(
    SIZEPROGREGEXP=r"^(?:\.text|\.text\.progmem|\.text\.itcm|\.data|\.text\.csf)\s+([0-9]+).*",
    SIZEDATAREGEXP=r"^(?:\.usbdescriptortable|\.dmabuffers|\.usbbuffers|\.data|\.bss|\.noinit|\.text\.itcm|\.text\.itcm\.padding)\s+([0-9]+).*"
)

env.Append(
    CPPDEFINES=[
        ("ARDUINO", 10805),
        ("TEENSYDUINO", int(FRAMEWORK_VERSION.split(".")[1])),
        "CORE_TEENSY"
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "cores", BUILD_CORE)
    ],

    LIBSOURCE_DIRS=[
        join(FRAMEWORK_DIR, "libraries")
    ]
)

if "BOARD" in env and BUILD_CORE == "teensy":
    env.Append(
        ASFLAGS=[
            "-mmcu=$BOARD_MCU"
        ],
        ASPPFLAGS=[
            "-x", "assembler-with-cpp",
        ],

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
            "-std=gnu++11",
            "-fpermissive"
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
elif "BOARD" in env and BUILD_CORE in ("teensy3", "teensy4"):
    env.Replace(
        AR="arm-none-eabi-gcc-ar",
        RANLIB="$AR"
    )

    env.Append(
        ASFLAGS=[
            "-mthumb",
            "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
        ],
        ASPPFLAGS=[
            "-x", "assembler-with-cpp",
        ],

        CCFLAGS=[
            "-Wall",  # show warnings
            "-ffunction-sections",  # place each function in its own section
            "-fdata-sections",
            "-mthumb",
            "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
            "-nostdlib"
        ],

        CXXFLAGS=[
            "-fno-exceptions",
            "-felide-constructors",
            "-fno-rtti",
            "-std=gnu++14",
            "-Wno-error=narrowing",
            "-fpermissive"
        ],

        CPPDEFINES=[
            ("F_CPU", "$BOARD_F_CPU"),
            "LAYOUT_US_ENGLISH"
        ],

        RANLIBFLAGS=["-s"],

        LINKFLAGS=[
            "-Wl,--gc-sections,--relax",
            "-mthumb",
            "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
            "-Wl,--defsym=__rtc_localtime=$UNIX_TIME"
        ],

        LIBS=["m", "stdc++"]
    )

    if not env.BoardConfig().get("build.ldscript", ""):
        env.Replace(LDSCRIPT_PATH=env.BoardConfig().get("build.arduino.ldscript", ""))
        
    if not env.BoardConfig().id_ in (
        "teensy40",
        "teensy41",
        "teensymm",
    ):
        env.Append(CCFLAGS=["-fsingle-precision-constant"])
        
    if env.BoardConfig().id_ in (
        "teensy35",
        "teensy36",
        "teensy40",
        "teensy41",
        "teensymm",
    ):
        fpv_version = "4-sp"
        if env.BoardConfig().id_.startswith(("teensy4", "teensymm")):
            fpv_version = "5"
            env.Append(CXXFLAGS=["-fno-threadsafe-statics"])

        env.Append(
            ASFLAGS=[
                "-mfloat-abi=hard",
                "-mfpu=fpv%s-d16" % fpv_version
            ],
            CCFLAGS=[
                "-mfloat-abi=hard",
                "-mfpu=fpv%s-d16" % fpv_version
            ],
            LINKFLAGS=[
                "-mfloat-abi=hard",
                "-mfpu=fpv%s-d16" % fpv_version
            ]
        )

    # Optimization
    if "TEENSY_OPT_FASTER_LTO" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-O2", "-flto", "-fno-fat-lto-objects"],
            LINKFLAGS=["-O2", "-flto", "-fno-fat-lto-objects", "-fuse-linker-plugin"]
        )
    elif "TEENSY_OPT_FAST" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-O1"],
            LINKFLAGS=["-O1"]
        )
    elif "TEENSY_OPT_FAST_LTO" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-O1", "-flto", "-fno-fat-lto-objects"],
            LINKFLAGS=["-O1", "-flto", "-fno-fat-lto-objects", "-fuse-linker-plugin"]
        )
    elif "TEENSY_OPT_FASTEST" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-O3"],
            LINKFLAGS=["-O3"]
        )
    elif "TEENSY_OPT_FASTEST_LTO" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-O3", "-flto", "-fno-fat-lto-objects"],
            LINKFLAGS=["-O3", "-flto", "-fno-fat-lto-objects", "-fuse-linker-plugin"]
        )
    elif "TEENSY_OPT_FASTEST_PURE_CODE" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-O3", "-mpure-code"],
            CPPDEFINES=["__PURE_CODE__"],
            LINKFLAGS=["-O3", "-mpure-code"]
        )
    elif "TEENSY_OPT_FASTEST_PURE_CODE_LTO" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-O3", "-mpure-code", "-flto", "-fno-fat-lto-objects"],
            CPPDEFINES=["__PURE_CODE__"],
            LINKFLAGS=["-O3", "-mpure-code", "-flto", "-fno-fat-lto-objects", "-fuse-linker-plugin"]
        )
    elif "TEENSY_OPT_DEBUG" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-g", "-Og"],
            LINKFLAGS=["-g", "-Og"]
        )
    elif "TEENSY_OPT_DEBUG_LTO" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-g", "-Og", "-flto", "-fno-fat-lto-objects"],
            LINKFLAGS=["-g", "-Og", "-flto", "-fno-fat-lto-objects", "-fuse-linker-plugin"]
        )
    elif "TEENSY_OPT_SMALLEST_CODE_LTO" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-Os", "--specs=nano.specs", "-flto", "-fno-fat-lto-objects"],
            LINKFLAGS=["-Os", "--specs=nano.specs", "-flto", "-fno-fat-lto-objects", "-fuse-linker-plugin"]
        )
    elif "TEENSY_OPT_FASTER" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-O2"],
            LINKFLAGS=["-O2"]
        )
    elif "TEENSY_OPT_SMALLEST_CODE" in env['CPPDEFINES']:
        env.Append(
            CCFLAGS=["-Os", "--specs=nano.specs"],
            LINKFLAGS=["-Os", "--specs=nano.specs"]
        )
    # default profiles
    else:
        # for Teensy LC => TEENSY_OPT_SMALLEST_CODE
        if env.BoardConfig().id_ == "teensylc":
            env.Append(
                CCFLAGS=["-Os", "--specs=nano.specs"],
                LINKFLAGS=["-Os", "--specs=nano.specs"]
            )
        # for others => TEENSY_OPT_FASTER
        else:
            env.Append(
                CCFLAGS=["-O2"],
                LINKFLAGS=["-O2"]
            )


cpu = env.BoardConfig().get("build.cpu", "")
if "cortex-m" in cpu:
    board = env.subst("$BOARD")
    math_lib = "arm_cortex%s_math"
    if board in ("teensy35", "teensy36"):
        math_lib = math_lib % "M4lf"
    elif board in ("teensy30", "teensy31"):
        math_lib = math_lib % "M4l"
    elif board.startswith(("teensy4", "teensymm")):
        math_lib = math_lib % "M7lfsp"
    else:
        math_lib = math_lib % "M0l"

    env.Prepend(LIBS=[math_lib])

    if cpu.startswith(("cortex-m4", "cortex-m0")):
        env.Append(
            ASFLAGS=[
                "-mno-unaligned-access",
            ],
            CCFLAGS=[
                "-mno-unaligned-access",
                "-fsingle-precision-constant"
            ],
            LINKFLAGS=[
                "-fsingle-precision-constant"
            ]
        )

# Teensy 2.x Core
if BUILD_CORE == "teensy":
    env.Append(CPPPATH=[join(FRAMEWORK_DIR, "cores")])

    # search relative includes in teensy directories
    core_dir = join(FRAMEWORK_DIR, "cores", "teensy")
    for item in sorted(listdir(core_dir)):
        file_path = join(core_dir, item)
        if not isfile(file_path):
            continue
        content = None
        content_changed = False
        with open(file_path, encoding="latin-1") as fp:
            content = fp.read()
            if '#include "../' in content:
                content_changed = True
                content = content.replace('#include "../', '#include "')
        if not content_changed:
            continue
        with open(file_path, "w", encoding="latin-1") as fp:
            fp.write(content)
else:
    env.Prepend(LIBPATH=[join(FRAMEWORK_DIR, "cores", BUILD_CORE)])

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
    join(FRAMEWORK_DIR, "cores", BUILD_CORE),
    src_filter="+<*> -<Blink.cc>"
))

env.Prepend(LIBS=libs)
