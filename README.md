# μDDO

![](./images/readme_example.png)

## Overview

A Linux launcher for the game Dungeons & Dragons Online, using Python and Qt6. Based on the now (unsupported?) PyLotRO launcher.

Links:
- https://www.ddo.com
- https://github.com/Lynx3d/pylotro
- http://sny.name/LOTRO/
- https://dungeonhelper.com/


## TODO
  - macros
    - add "type" command
    - add "enter" alias
    - add interleaving of macros
  - python-PS module for getting pid and killing processes
  - add window audio muting options
  - remove lingering xdotool stuff
  - update screenshot
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
    - currently only one instance of Dungeon Helper can be managed, because tDHPIDWatcher 
    only looks processes containing DungeonHelper.exe and takes the PID of first thing
    it finds. This means that killing one of them kills all of them.
    - maybe migrate back to single instance of DungeonHelper?

## Macros Daemon

I have added a shortcuts/macro daemon, something severely lacking in the game itself. This has been recently updated to rely on the Milvian plugin for Dungeon Helper, so it will depend on that. 

I tried to keep it as flexible as possible, so as a result, it is a bit complicated. Shortcuts are grouped into "sets". Each set can be toggled on/off by clicking the checkbox next to their name.

#### Create a Macro Set
  A Macro Set is a "collection" of triggers and their actions. Each Set can be activated/deactivated individually by toggling the checkbox to the left of their name. With that you can, for instance, create a Macro Set for each individual character and turn it on/off depending on who you have online in your party at the moment.

  To rename a set, doubleclick its entry in the list (automatically named as NewSetX) and edit the text in-line. 

#### Add a Macro to the Set
  All macros associated with the currently selected set are displayed in the table widget. Click the "+" button to the right side of the table to add a new shortcut entry (or the "-" to delete the currently selected row).
  
  - icon: not yet implemented
  - name: just a reference for yourself, it is not used internally (yet?)
  - trigger: when these keys are pressed, an action will be triggered
    - syntax is `<modifier1>+<modifier2>+...+<key>`. Examples: z, ctrl+a, shift+alt+f2, or pageup
    - do not use spaces!
    - valid modifiers are `shift`, `ctrl`, `alt`, `super`, `win`, `meta`, as well as `mod1` to `mod5`. Depending on your keyboard configuration, some of these modifiers might be misinterpreted, so test extensively.
    - `<key>` is anything from `/usr/include/X11/keysymdef.h` without the `XK_` prefix, e.g. NumPad keys are KP_0 to KP_9, KP_Divide, KP_Subtract, etc. I made them case-insensitive and caps lock-insensitive.
  - action: 
      - syntax is `<script1>; <script2>; <script3>;`
      - each script is formatted as `<target1>, ..., <targetN>: <action1>, ..., <actionM>`. The comma is optional, and a simple space can be used instead.
          - [TODO] add "self" target, which focuses the account which was active when the trigger was pressed
      - each `<target>` is a character. If the account is not logged in, or there is a typo in the name, it will be silently ignored.
      - each `<action>` can be:
          - the keyword `sleep_X` which will cause the daemon to sleep for X seconds before executing the next action. X can be a float, e.g. `sleep_0.75`
          - any input from VoK.Sdk.Enum.Ddo.InputActions converted lower case. I am providing a list in the file VoK.Sdk.Enum.Ddo.InputActions.txt, but those are subject to change.
          - I added extra aliases for the shortcut bars: SHORTCUT_BARX_KEYY is accessible simply via bxky. 
          - [TODO] the keyword `macro_Z` will trigger the action associated with shortcut Z
          - [TODO] the keyword `macro_{name}` will trigger the action associated with the macro {name}

  #### [Optional] Aliases
  As a convenience tool, I added the option to create aliases for things that you might end up writing very often. On the Aliases widget, click the "+" button to add a new entry and just edit the values directly in the list. 

  You can use aliases in the triggers or actions of any macro. They are substituted 1:1 before any further parsing of the text. Example: assume the alias "ca = ctrl+alt+" was added and that a shortcut has the trigger "cab". This will be translated as "ctrl+alt+b" before anything else is done. 

  Aliases are a great way to mess up the whole system, so check the logs (see below) if something is not working as you expected. Specially, make sure you're being careful with spaces. Aliases are replaced in the order they are given, so if you put the alias "a=1" before the alias "aaa=3" in the list, it will convert "baaab" into "b111b", not into "b3b". If you add "aaa=3" before "a=1", it will indeed convert "baaab" into "b3b".

  Aliases are not saved automatically. This is intentional. Press "Save" button on the right side of the Widget to save all modifications to file, or "Reload" to revert changes.

  #### Starting the Daemon
  The daemon will grab all the active sets (i.e. enabled via the checkbox) and parse them all immediatelly when activated. Check `~/.config/muDDO/log` for details about the parsing. Any changes while the daemon is running are ignored, but you can restart it to trigger the new settings (without restarting the game or even having to save the changes).
  
  Use right-click on the "Macros Daemon" main orb-button to open a context menu or ctrl+click to force a purge+restart of the Daemon. It iterates over all possible trigger and modifier combinations and "ungrabs" them one by one. It takes a good second to do that.

  #### Sets Consolidation:
  When activated, the Daemon will consolidate all active sets. This includes checking which triggers appear in multiple sets. If this happens, it will merge actions from all active sets associated with the same trigger. This is intentional. 
  
  #### Saving changes:
  The daemon doesn't save macros automatically. This is intentional. Select a set and click "Save" button to save the changes into file, or ctrl+click the "Save" button to save all sets (active or not). You can also experiment with new sets and combinations and click the "Reload" button in case something goes wrong.

  IMPORTANT: the sets are saved by default in `~/.config/muDDO/macros/<name>.macro` as a JSON file, so don't use strange characters in the filename that would interfere with the Linux naming convention.

## License

This is licensed under GPL-3 license. See https://www.gnu.org/licenses/ for details.

## About "Lord of the Rings Online" Support

I removed the support to LotRO simply because I could not test it. The added complexity should be small, if anyone is interested in expanding the app for LoTRO too.

## About Windows and/or MacOS Support

I couldn't care less about other platforms (i.e. reciprocity). You are welcome to do the porting/testing/maintaining for other platforms (please notice the GPL-3 license).
