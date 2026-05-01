# μDDO

![](./docs/readme_example.png)

## Overview

A Linux launcher for the game Dungeons & Dragons Online, using Python and Qt6. Based on the now (unsupported?) PyLotRO launcher.

## Features
Currently implemented features:
 - launching the game and managing multiple (no upper limit) accounts at once
 - manages all processes/instances launched, including terminate, kill, restart, etc
 - basic X window management of game windows: save position and border status and restores them
   - no Wayland support and no plans for it
 - basic Pipewire support for Audio muting/unmuting (you don't want all game instances narrating the dungeon, do you?)
 - patching
    - quick or full patching (calls original launcher)
 - basic [Dungeon Helper](https://dungeonhelper.com/) integration (must be installed separately)
 - basic [Macro'ing](docs/Macros.md) capabilities, see docs for details on capabilities. Requires [Dungeon Helper](https://dungeonhelper.com/) and μDDO's custom Milvian plugin
    - set to global shortcuts
    - set to μDDO's toolbar (e.g. for occasional and not urgent macros)
 - support for inventory management via Milvian (alpha stage)
    - fetches current inventory information
    - advanced filtering in the local UI
    - batch-dissolving of selected items
    - batch-selling (mark as junk) of selected items
    - repair-all, sell gems also enabled

## TODO
  - update README's screenshot
  - Milvian Bridge (Macros Daemon)
    - add number of active bridges/sets in "summary"
    - add complex macros
      - allow loops
      - allow branches
      - allow asynchronous behaviour
      - allow check state (e.g. cooldown)
    - UI improvements
      - create context menu with all existing macros (so that they don't need a keyboard shortcut)
      - vizualize keyboard with its macros
  - Inventory Manager
    - enable storing list of itemIds to currently opened container/bank
    - enable trading
    - enable tracking of last known state for each container/character/bank (like Trove Plugin)
  - cToolbar:
    - re-implement "fill rows first"
    - make all buttons "turn off" when milvian bridge stops
  - Other 
    - aProcessItems refactor?
      - use a QTableWidget or QListWidget instead?
    - implement news visualization
    - use keyring to store passwords instead of plain text format
    - test the launcher with Wine (currently tested with Steam Proton)
    - add cmd line option for verbosity
    - maybe add support for downloading/installing DungeonHelper.exe?

## License

This is licensed under GPL-3 license. See https://www.gnu.org/licenses/ for details.

## About "Lord of the Rings Online" Support

I removed the support to LotRO simply because I could not test it. The added complexity should be small, if anyone is interested in expanding the app for LoTRO too.

## About Windows and/or MacOS Support

I couldn't care less about Windows and/or MacOS (a.k.a. reciprocity 😉). You are welcome to do the porting/testing/maintaining for other platforms, but please notice that you'll be bound to the GPL-3 license.

## Links:
- https://www.ddo.com
- https://github.com/Lynx3d/pylotro
- http://sny.name/LOTRO/
- https://github.com/Maetrim/DDOBuilderV2 
  - has pretty much all DDO icons you could ever wish for