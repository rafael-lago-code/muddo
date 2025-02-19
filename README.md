# μDDO

## Overview

An Linux-based launcher for the game Dungeons & Dragons Online, using Python and Qt6. Based on the now (unsupported?) PyLotRO launcher.

Links:
- https://www.ddo.com
- https://github.com/Lynx3d/pylotro
- https://dungeonhelper.com/


## TODO
- Implement the patching capabilities
- Implement news visualization
- use keyring to store passwords instead of plain text format
- Test the launcher with Wine (currently tested with Steam Proton)
- Create settings to enable/disable xdotool and check if it is available
- Use GameDir instead of GameExec (which is currently hard-coded)
- Integrate DungeonHelper launching, if it is installed

## License

This is licensed under GPL-3 license. See https://www.gnu.org/licenses/ for details.

## About "Lord of the Rings Online" Support

I removed the support to LotRO simply because I could not test it. The added complexity should be small.

## About Windows and/or MacOS Support

You are welcome to do the porting/testing for other platforms (please notice the GPL-3 license).