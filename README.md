# μDDO

![](./images/readme_example.png)

## Overview

An Linux-based launcher for the game Dungeons & Dragons Online, using Python and Qt6. Based on the now (unsupported?) PyLotRO launcher.

Links:
- https://www.ddo.com
- https://github.com/Lynx3d/pylotro
- http://sny.name/LOTRO/
- https://dungeonhelper.com/


## TODO
- implement the patching capabilities
  - the first patching (when you install the game) doesn't seem to be working, but subsequent patches seem to be fine
- migrate the game launcher from os.system to subprocess
  - currently it doesn't start but also doesn't show any specific error
- implement news display
- use keyring to store passwords instead of plain text format
- test the launcher with Wine (currently tested with Steam Proton)
- add cmd line option for verbosity
- finalize DungeonHelper support
  - maybe add support for downloading/installing DungeonHelper.exe?

## License

This is licensed under GPL-3 license. See https://www.gnu.org/licenses/ for details.

## About "Lord of the Rings Online" Support

I removed the support to LotRO simply because I could not test it. The added complexity should be small, if anyone is interested in doing that.

## About Windows and/or MacOS Support

You are welcome to do the porting/testing for other platforms (please notice the GPL-3 license).
