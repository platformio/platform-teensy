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

from os.path import isfile, join

from SCons.Script import (COMMAND_LINE_TARGETS, AlwaysBuild, Builder, Default,
                          DefaultEnvironment)

env = DefaultEnvironment()
platform = env.PioPlatform()

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
        ("F_CPU", "$BOARD_F_CPU"),
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
                action=env.VerboseAction(" ".join([
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
                    "$TARGET"
                ]), "Building $TARGET"),
                suffix=".eep"
            ),

            ElfToHex=Builder(
                action=env.VerboseAction(" ".join([
                    "$OBJCOPY",
                    "-O",
                    "ihex",
                    "-R",
                    ".eeprom",
                    "$SOURCES",
                    "$TARGET"
                ]), "Building $TARGET"),
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
        LIBS=[
            "c", "gcc", "arm_cortex%sl_math" %
            ("M4" if env.BoardConfig().get(
                "build.cpu") == "cortex-m4" else "M0")
        ],
        BUILDERS=dict(
            ElfToBin=Builder(
                action=env.VerboseAction(" ".join([
                    "$OBJCOPY",
                    "-O",
                    "binary",
                    "$SOURCES",
                    "$TARGET"
                ]), "Building $TARGET"),
                suffix=".bin"
            ),
            ElfToHex=Builder(
                action=env.VerboseAction(" ".join([
                    "$OBJCOPY",
                    "-O",
                    "ihex",
                    "-R",
                    ".eeprom",
                    "$SOURCES",
                    "$TARGET"
                ]), "Building $TARGET"),
                suffix=".hex"
            )
        )
    )
    if env.BoardConfig().id_ in ("teensy35", "teensy36"):
        env.Append(
            LINKFLAGS=["-mfloat-abi=hard", "-mfpu=fpv4-sp-d16"],
            CCFLAGS=["-mfloat-abi=hard", "-mfpu=fpv4-sp-d16"]
        )

env.Append(
    ASFLAGS=env.get("CCFLAGS", [])[:]
)

if isfile(
        join(
            platform.get_package_dir("tool-teensy") or "",
            "teensy_loader_cli")):
    env.Append(
        UPLOADER="teensy_loader_cli",
        UPLOADERFLAGS=[
            "-mmcu=$BOARD_MCU",
            "-w",  # wait for device to apear
            "-s",  # soft reboot if device not online
            "-v"  # verbose output
        ],
        UPLOADHEXCMD='$UPLOADER $UPLOADERFLAGS $SOURCES')
else:
    env.Append(
        REBOOTER="teensy_reboot",
        UPLOADER="teensy_post_compile",
        UPLOADERFLAGS=[
            "-file=firmware", '-path=$BUILD_DIR',
            '-tools=%s' % (platform.get_package_dir("tool-teensy") or "")
        ],
        UPLOADHEXCMD='$UPLOADER $UPLOADERFLAGS')

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_firm = join("$BUILD_DIR", "firmware.hex")
else:
    target_elf = env.BuildProgram()
    target_firm = env.ElfToHex(join("$BUILD_DIR", "firmware"), target_elf)

AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm, target_firm)

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)

#
# Target: Upload by default firmware file
#

target_upload = env.Alias(
    "upload", target_firm,
    [env.VerboseAction("$UPLOADHEXCMD", "Uploading $SOURCE")] +
    ([env.VerboseAction("$REBOOTER", "Rebooting...")]
     if "REBOOTER" in env else []))
AlwaysBuild(target_upload)

#
# Default targets
#

Default([target_buildprog, target_size])
