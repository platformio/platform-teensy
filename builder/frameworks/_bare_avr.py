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

#
# Default flags for bare-metal programming (without any framework layers)
#

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()

machine_flags = [
    "-mmcu=$BOARD_MCU"
]

env.Append(
    ASFLAGS=machine_flags,
    ASPPFLAGS=[
        "-x", "assembler-with-cpp",
    ],
    CCFLAGS=machine_flags + [
        "-Os",  # optimize for size
        "-Wall",  # show warnings
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
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

    LINKFLAGS=machine_flags + [
        "-Os",
        "-Wl,--gc-sections,--relax",
    ],

    LIBS=["m"]
)
