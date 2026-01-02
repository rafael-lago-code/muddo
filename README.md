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
 - Shortcuts
   - add click
   - add "type" command
   - add "enter" alias
   - add custom aliases
   - add advanced macros
   - add interleaving of macros
   - write documentation
 - python-PS module for getting pid and killing processes
 - add window audio muting options
 - remove lingering xdotool stuff
 - update example.

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
  - currently only one instance of Dungeon Helper can be managed, because tDHPIDWatcher 
  only looks processes containing DungeonHelper.exe and takes the PID of first thing
  it finds. This means that killing one of them kills both of them.
  - maybe migrate back to single instance of DungeonHelper?

## Shortcuts Daemon

I have added a shortcuts/macro daemon, something severely lacking in the game itself. It is rather poor and it works by sending xtext_fake_input signals to the focused windows (because Wine and its derivatives ignore anything that goes on unfocused windows *-by constrcution-*)

I tried to keep it as flexible as possible, so as a result, it is a bit complicated. Shortcuts are grouped into "sets". Each set can be toggled on/off by clicking the checkbox

#### Create a Shortcut Set
  A Shortcut Set is a "collection" of triggers and their actions. Each Set can be activated/deactivated individually by toggling the checkbox to the left of their name. With that you can, for instance, create a Shortcut Set for each individual character and turn it on/off depending on who you have online in your party at the moment.

  To rename a set, doubleclick its entry in the list (automatically named as NewSetX) and edit the text in-line. 

#### Add a Shortcut to the Set
  All shortcuts associated with the currently selected set are displayed in the table widget. Click the "+" button to the right side of the table to add a new shortcut entry (or the "-" to delete the currently selected row).
  
  - icon: not yet implemented
  - name: just a reference for yourself, it is not used internally
  - trigger: when these keys are pressed, an action will be triggered
    - syntax is `<modifier1>+<modifier2>+...+<key>`. Examples: z, ctrl+a, shift+alt+f2, or pageup
    - do not use spaces!
    - valid modifiers are `shift`, `ctrl`, `alt`, `super`, `win`, `meta`, as well as `mod1` to `mod5`. Depending on your keyboard configuration, some of these modifiers might be misinterpreted, so test extensively.
    - `<key>` is anything from `/usr/include/X11/keysymdef.h` without the `XK_` prefix, e.g. NumPad keys are KP_0 to KP_9, KP_Divide, KP_Subtract, etc. I made them case-insensitive and caps lock-insensitive.
  - action: 
      - syntax is `<script1>; <script2>; <script3>;`
      - each script is formatted as `<target1>, ..., <targetN>: <action1>, ..., <actionM>`. The comma is optional, and a simple space can be used instead.
          - [TODO] add "all" target
          - [TODO] add "self" target, which focuses the account which was active when the trigger was pressed
      - each `<target>` is a game account. The daemon will send the actions to the window associated with this account. If the account is not online, or there is a typo in the name, it will be silently ignored.
      - each `<action>` can be:
          - a keystroke (following the exact same syntax as the "trigger"). Do not use spaces, as they will be interpreted as different actions! For instance, "shift + a" will be interpreted as three different actions, one of which (namely "+") is invalid.
          - the keyword `sleep_X` which will cause the daemon to sleep for X seconds before executing the next action. X can be a float, e.g. `sleep_0.75`
          - [TODO] the keyword `focus_<target>` which will cause the daemon to change send the next signals to `<target>` instead.
          - the keyword `click_Y` which will trigger a mouse click with the button Y. Buttons 1, 2 and 3 are respectivelly left, middle and right mouse buttons. Buttons 4 and 5 are scroll up and down respectivelly. The daemon doesn't check if the button exists, so `click_13` is valid (but may do nothing or cause unexpected results)
          - [TODO] the keyword `macro_Z` will trigger the action associated with shortcut Z

  #### [Optional] Aliases
  As a convenience tool, I added the option to create aliases for things that you might end up writing very often. On the Aliases widget, click the "+" button to add a new entry and just edit the values directly in the list. 

  You can use aliases in the triggers or actions of any shortcuts. They are substituted 1:1 before any further parsing of the text. Example: assume the alias "ca = ctrl+alt+" was added and that a shortcut has the trigger "cab". This will be translated as "ctrl+alt+b" before anything else is done. 

  Aliases are a great way to mess up the whole system, so check the logs (see below) if something is not working as you expected. Specially, make sure you're being careful with spaces. An alias such as " word=shift+c" will turn "a b word" into "a bshift+c" which is probably not what you wanted. Similarly, "Z=sleep_1" and "ZZ=sleep_2" will actually translate "ZZ" into "sleep_1sleep_1" which is likely not what you wanted either. 

  Aliases are not saved automatically. This is intentional. Press "Save" button on the right side of the Widget to save all modifications to file, or "Reload" to revert changes.

  #### Starting the Daemon
  The daemon will grab all the active sets (i.e. enabled via the checkbox) and parse them all immediatelly when activated. Check `~/.config/muDDO/log` for details about the parsing. Any changes while the daemon is running are ignored, but you can restart it to trigger the new settings (without restarting the game or even having to save the changes)

  #### Sets Consolidation:
  When activated, the Daemon will consolidate all active sets. This includes checking which triggers appear in multiple sets. If this happens, it will merge actions from all active sets associated with the same trigger. This is intentional. 
  
  #### Saving changes:
  The daemon doesn't save shortcuts automatically. This is intentional. Select a set and click "Save" button to save the changes into file, or ctrl+click the "Save" button to save all sets (active or not). You can also experiment with new sets and combinations and click the "Reload" button in case something goes wrong.

  IMPORTANT: the sets are saved by default in `~/.config/muDDO/shortcuts/<name>.shortcuts` as a JSON file, so don't use strange characters in the filename that would interfere with the Linux naming convention.




## License

This is licensed under GPL-3 license. See https://www.gnu.org/licenses/ for details.

## About "Lord of the Rings Online" Support

I removed the support to LotRO simply because I could not test it. The added complexity should be small, if anyone is interested in doing that.

## About Windows and/or MacOS Support

You are welcome to do the porting/testing for other platforms (please notice the GPL-3 license).
