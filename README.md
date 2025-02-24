# μDDO

![](./images/readme_example.png)

## Overview

An Linux-based launcher for the game Dungeons & Dragons Online, using Python and Qt6. Based on the now (unsupported?) PyLotRO launcher.

Links:
- https://www.ddo.com
- https://github.com/Lynx3d/pylotro
- https://dungeonhelper.com/


## TODO
- implement the patching capabilities
- implement news visualization
- use keyring to store passwords instead of plain text format
- test the launcher with Wine (currently tested with Steam Proton)
- use GameDir instead of GameExec (which is currently hard-coded)
- add context menu for launch button for selecting profiles
- add cmd line option for verbosity
- finalize DungeonHelper support
  - maybe add support for downloading/installing DungeonHelper.exe?

## License

This is licensed under GPL-3 license. See https://www.gnu.org/licenses/ for details.

## About "Lord of the Rings Online" Support

I removed the support to LotRO simply because I could not test it. The added complexity should be small, if anyone is interested in doing that.

## About Windows and/or MacOS Support

You are welcome to do the porting/testing for other platforms (please notice the GPL-3 license).
