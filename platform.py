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

import sys

from platformio.public import PlatformBase


IS_WINDOWS = sys.platform.startswith("win")


class TeensyPlatform(PlatformBase):

    def configure_default_packages(self, variables, targets):
        if variables.get("board"):
            board_config = self.board_config(variables.get("board"))
            del_toolchain = "toolchain-gccarmnoneeabi"
            if board_config.get("build.core") != "teensy":
                del_toolchain = "toolchain-atmelavr"
            if del_toolchain in self.packages:
                del self.packages[del_toolchain]

        frameworks = variables.get("pioframework", [])
        if "arduino" in frameworks:
            self.packages.pop("toolchain-gccarmnoneeabi", None)
        else:
            self.packages["toolchain-gccarmnoneeabi"]["optional"] = False
            self.packages.pop("toolchain-gccarmnoneeabi-teensy", None)

        if "zephyr" in frameworks:
            for p in self.packages:
                if p in ("tool-cmake", "tool-dtc", "tool-ninja"):
                    self.packages[p]["optional"] = False
            if not IS_WINDOWS:
                self.packages["tool-gperf"]["optional"] = False
        elif "arduino" in frameworks and board_config.get("build.core", "") == "teensy4":
            self.packages["tool-teensy"]["optional"] = False

        # configure J-LINK tool
        jlink_conds = [
            "jlink" in variables.get(option, "")
            for option in ("upload_protocol", "debug_tool")
        ]
        if variables.get("board"):
            board_config = self.board_config(variables.get("board"))
            jlink_conds.extend([
                "jlink" in board_config.get(key, "")
                for key in ("debug.default_tools", "upload.protocol")
            ])
        jlink_pkgname = "tool-jlink"
        if not any(jlink_conds) and jlink_pkgname in self.packages:
            del self.packages[jlink_pkgname]

        return super().configure_default_packages(variables, targets)

    def get_boards(self, id_=None):
        result = super().get_boards(id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key in result:
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        upload_protocols = board.manifest.get("upload", {}).get(
            "protocols", [])
        if "tools" not in debug:
            debug["tools"] = {}

        if "jlink" in upload_protocols and "jlink" not in debug["tools"]:
            assert debug.get("jlink_device"), (
                "Missed J-Link Device ID for %s" % board.id)
            debug["tools"]["jlink"] = {
                "server": {
                    "package": "tool-jlink",
                    "arguments": [
                        "-singlerun",
                        "-if", "SWD",
                        "-select", "USB",
                        "-device", debug.get("jlink_device"),
                        "-port", "2331"
                    ],
                    "executable": ("JLinkGDBServerCL.exe"
                                   if IS_WINDOWS else
                                   "JLinkGDBServer")
                }
            }

        board.manifest["debug"] = debug
        return board

    def configure_debug_session(self, debug_config):
        if debug_config.speed:
            if "jlink" in (debug_config.server or {}).get("executable", "").lower():
                debug_config.server["arguments"].extend(
                    ["-speed", debug_config.speed]
                )
