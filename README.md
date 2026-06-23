# μDDO
![](./docs/mainOrbUI.png)

## Overview

A powerful Linux launcher for the game Dungeons & Dragons Online, using Python and Qt6. Based on the now (unsupported?) PyLotRO launcher.

## Features
 - full multiaccount support (no upper limit)
 - manages all processes/instances launched, including terminate, kill, restart, etc
 - basic X window management of game windows: save position, border status and restores them
   - no Wayland support and no plans for it
   - fixes blackscreen bug for WMs which suffer from it
 - basic Pipewire support for Audio muting/unmuting (you don't want all game instances narrating the dungeon, do you?)
 - patching & news
    - quick patching or full patching (calls original launcher)
    - displays same news as the original launcher
 - basic [Dungeon Helper](https://dungeonhelper.com/) integration (must be installed separately)
 - [Macro'ing](docs/Macros.md) via Milvian Bridges, see docs for details on capabilities. Requires [Dungeon Helper](https://dungeonhelper.com/) and μDDO's custom Milvian plugin
 - Storage management via Milvian
    - fetches current inventory information
    - batch-dissolving, selling (mark as junk), storing or using of selected items
    - repair-all, sell gems also enabled
    - advanced filtering in the local UI
 - Strategy management via Milvian
    - basic follow (analogous to Dungeon Helper's AAF)
    - follows jump, swim, direction (but not camera pitch), target selection and ladder behaviour
    - accept quest share, party invite and ressurrection
    - local leader only:
      - follows into most quests instance ("followPortal" but not really a portal)
      - follows recall
    - splitting of roles - assigning a commander and a captain to the party
    - advanced and fully functional shortcut configuration support for all of the above
 - Map
    - added basic support, still working icons and refresh rate
    - shows usual map pins, plus entities (monsters, breakeables, etc)


## TODO
  - Macros Daemon
    - add number of active bridges/sets in "main UI->summary"
    - add complex macros
      - allow loops, branches, conditionals, check states (e.g. cooldown) and equipment
        - example usecase: cast Flame Arrow, change gear, cast initial buffs at the beginning of each dungeon
      - revamp the macros parsing (i.e. "consolidation") because it is super messy and difficult to debug now
        - use μString to simplify things (a lot)
    - enable macro(*) macros
    - enable menu macros
    - UI improvements
      - vizualize keyboard with its macros
  - Map
    - figure out distinction between:
      - normal monsters vs bosses
        - boss, raid, mini-boss, rare encounters, etc
      - champions and normal monsters
        - between champion ranks
    - distinguish own pet from other pets
    - allow entering "commander" and "leader" in the list of sources
  - Milvian
    - Bug: if you log in a different characters with Milvian Plugin on, it doesn't update the bridge path
    - re-think initialization of Milvian Bridges; it should be done automatically when a character logs in
    - needs to signal logouts/death of process somehow
    - maybe leave signal in χDispatcher until something happens? File watcher to see new files creation? 
  - Strategy
    - sometimes drag-and-drop doesn't work, debug that further
    - implement "save" reserved word for strateg() command
    - implement "followPortal"
      - already working, but needs to follow closePortal too
    - fix and test further "closeExplorerJournals"
      - OnExplorer event is for something else, explorer journals seem to have no property, they are not fired when OnSelectedObject... I have no idea how to proceed here.
    - Nice to have:
      - implement "followMount"
        - currently detects but fails to send the "mount" input (cannot find the hotkey for it!)
        - implement dismount as well
        - maybe unnecessary for this framework
      - implement "followBlock" (and most importantly: UNBLOCK!!!!), "followTeleport" (items like key to estar and the D12),  "followSneak", "shareLoot"
  - Storage Manager
    - enable sorting
    - enable tracking inside of containers (i.e. bags)
      - more advanced features: sharing of collectibles and ingredients
    - enable tracking of last known state for each container/character/bank (like Trove Plugin)
  - MiniBrowser
    - a low-feature ad-blocking minibrowser that automatically opens to the wiki page of the current quest or currently selected item
  - Revamp/merge accounts/processmanager
    - aProcessItems refactor?
      - use a QTableWidget or QListWidget instead?
    - use keyring to store passwords instead of plain text format
  - Other 
    - test the launcher with Wine (currently tested with Steam Proton)
    - add cmd line option for verbosity
    - maybe add support for downloading/installing DungeonHelper.exe and the game itself

## License

This is licensed under GPL-3 license. See https://www.gnu.org/licenses/ for details.

## About "Lord of the Rings Online" Support

I removed the support to LotRO from the launcher simply because I could not test it. The added complexity for the launcher portion should be small, if anyone is interested in expanding for LoTRO too. For Milvian and everything depending on it (Macros, Storage, Strategy, etc) it probably requires a major review or even a rewrite.

## About Windows and/or MacOS Support

I couldn't care less about Windows and/or MacOS (a.k.a. reciprocity 😉). You are welcome to do the porting/testing/maintaining for other platforms, but please notice that you'll be bound to the GPL-3 license.

## Thanks to
"Benny Enny" for his pre-alpha-stage-testing of several of the features and continuous feedback. 

## Links:
- https://www.ddo.com
- https://github.com/Lynx3d/pylotro
- http://sny.name/LOTRO/
- https://github.com/Maetrim/DDOBuilderV2 
  - has pretty much all DDO icons you could ever wish for