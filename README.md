# Teensy: development platform for [PlatformIO](https://platformio.org)

[![Build Status](https://github.com/platformio/platform-teensy/workflows/Examples/badge.svg)](https://github.com/platformio/platform-teensy/actions)

Teensy is a complete USB-based microcontroller development system, in a very small footprint, capable of implementing many types of projects. All programming is done via the USB port. No special programmer is needed, only a standard USB cable and a PC or Macintosh with a USB port.

* [Home](https://registry.platformio.org/platforms/platformio/teensy) (home page in the PlatformIO Registry)
* [Documentation](https://docs.platformio.org/page/platforms/teensy.html) (advanced usage, packages, boards, frameworks, etc.)

# Usage

1. [Install PlatformIO](https://platformio.org)
2. Create PlatformIO project and configure a platform option in [platformio.ini](https://docs.platformio.org/page/projectconf.html) file:

## Stable version

```ini
[env:stable]
platform = teensy
board = ...
...
```

## Development version

```ini
[env:development]
platform = https://github.com/platformio/platform-teensy.git
board = ...
...
```

# Configuration

Please navigate to [documentation](https://docs.platformio.org/page/platforms/teensy.html).
