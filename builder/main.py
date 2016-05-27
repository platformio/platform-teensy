# Copyright 2014-present Ivan Kravets <me@ikravets.com>
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
    Builder for Teensy boards
"""

from os.path import isfile, join

from SCons.Script import (COMMAND_LINE_TARGETS, AlwaysBuild, Builder, Default,
                          DefaultEnvironment)

env = DefaultEnvironment()
platform = env.DevPlatform()

env.Replace(
    ARFLAGS=["rcs"],

    ASFLAGS=["-x", "assembler-with-cpp"],

    CCFLAGS=[
        "-g",  # include debugging info (so errors include line numbers)
        "-Os",  # optimize for size
        "-Wall",  # show warnings
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections"
    ],

    CXXFLAGS=[
        "-fno-exceptions",
        "-std=gnu++0x",
        "-felide-constructors"
    ],

    CPPDEFINES=[
        "F_CPU=$BOARD_F_CPU",
        "USB_SERIAL",
        "LAYOUT_US_ENGLISH"
    ],

    LINKFLAGS=[
        "-Os",
        "-Wl,--gc-sections,--relax"
    ],

    LIBS=["m"],

    PROGNAME="firmware",
    PROGSUFFIX=".elf"
)

if "BOARD" in env and env.BoardConfig().get("build.core") == "teensy":
    env.Replace(
        AR="avr-ar",
        AS="avr-as",
        CC="avr-gcc",
        CXX="avr-g++",
        OBJCOPY="avr-objcopy",
        RANLIB="avr-ranlib",
        SIZETOOL="avr-size",
        SIZEPRINTCMD='$SIZETOOL --mcu=$BOARD_MCU -C -d $SOURCES'
    )
    env.Append(
        CCFLAGS=[
            "-mmcu=$BOARD_MCU"
        ],
        CXXFLAGS=[
            "-fno-threadsafe-statics"
        ],
        LINKFLAGS=[
            "-mmcu=$BOARD_MCU"
        ],
        BUILDERS=dict(
            ElfToEep=Builder(
                action=" ".join([
                    "$OBJCOPY",
                    "-O",
                    "ihex",
                    "-j",
                    ".eeprom",
                    '--set-section-flags=.eeprom="alloc,load"',
                    "--no-change-warnings",
                    "--change-section-lma",
                    ".eeprom=0",
                    "$SOURCES",
                    "$TARGET"]),
                suffix=".eep"
            ),

            ElfToHex=Builder(
                action=" ".join([
                    "$OBJCOPY",
                    "-O",
                    "ihex",
                    "-R",
                    ".eeprom",
                    "$SOURCES",
                    "$TARGET"]),
                suffix=".hex"
            )
        )
    )
elif "BOARD" in env and env.BoardConfig().get("build.core") == "teensy3":
    env.Replace(
        AR="arm-none-eabi-ar",
        AS="arm-none-eabi-as",
        CC="arm-none-eabi-gcc",
        CXX="arm-none-eabi-g++",
        OBJCOPY="arm-none-eabi-objcopy",
        RANLIB="arm-none-eabi-ranlib",
        SIZETOOL="arm-none-eabi-size",
        SIZEPRINTCMD='$SIZETOOL -B -d $SOURCES',
    )
    env.Append(
        CCFLAGS=[
            "-mthumb",
            "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
            "-nostdlib",
            "-fsingle-precision-constant"
        ],
        CXXFLAGS=[
            "-fno-rtti"
        ],
        LINKFLAGS=[
            "-mthumb",
            "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
            "-Wl,--defsym=__rtc_localtime=$UNIX_TIME",
            "-fsingle-precision-constant",
            "--specs=nano.specs"
        ],
        LIBS=["c", "gcc"],
        BUILDERS=dict(
            ElfToBin=Builder(
                action=" ".join([
                    "$OBJCOPY",
                    "-O",
                    "binary",
                    "$SOURCES",
                    "$TARGET"]),
                suffix=".bin"
            ),
            ElfToHex=Builder(
                action=" ".join([
                    "$OBJCOPY",
                    "-O",
                    "ihex",
                    "-R",
                    ".eeprom",
                    "$SOURCES",
                    "$TARGET"]),
                suffix=".hex"
            )
        )
    )

env.Append(
    ASFLAGS=env.get("CCFLAGS", [])[:]
)


if isfile(join(platform.get_package_dir("tool-teensy") or "",
               "teensy_loader_cli")):
    env.Append(
        UPLOADER="teensy_loader_cli",
        UPLOADERFLAGS=[
            "-mmcu=$BOARD_MCU",
            "-w",  # wait for device to apear
            "-s",  # soft reboot if device not online
            "-v"   # verbose output
        ],
        UPLOADHEXCMD='$UPLOADER $UPLOADERFLAGS $SOURCES'
    )
else:
    env.Append(
        REBOOTER="teensy_reboot",
        UPLOADER="teensy_post_compile",
        UPLOADERFLAGS=[
            "-file=firmware",
            '-path="$BUILD_DIR"',
            '-tools="%s"' % (platform.get_package_dir("tool-teensy") or "")
        ],
        UPLOADHEXCMD='$UPLOADER $UPLOADERFLAGS'
    )

#
# Target: Build executable and linkable firmware
#

target_elf = env.BuildProgram()

#
# Target: Build the firmware file
#

if "uploadlazy" in COMMAND_LINE_TARGETS:
    target_firm = join("$BUILD_DIR", "firmware.hex")
else:
    target_firm = env.ElfToHex(join("$BUILD_DIR", "firmware"), target_elf)

#
# Target: Print binary size
#

target_size = env.Alias("size", target_elf, "$SIZEPRINTCMD")
AlwaysBuild(target_size)

#
# Target: Upload by default firmware file
#

upload = env.Alias(
    ["upload", "uploadlazy"], target_firm,
    ["$UPLOADHEXCMD"] + (["$REBOOTER"] if "REBOOTER" in env else []))
AlwaysBuild(upload)

#
# Target: Unit Testing
#

AlwaysBuild(env.Alias("test", [target_firm, target_size]))

#
# Target: Define targets
#

Default([target_firm, target_size])
