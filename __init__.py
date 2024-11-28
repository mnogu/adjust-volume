# Anki 2.1.x add-on to adjust the sound volume
# Copyright (C) 2021  Muneyuki Noguchi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Adjust the sound volume in 2.1.x.
"""

if __name__ == "__main__":
    pass
else:
    from aqt import gui_hooks
    from aqt import mw
    from aqt.qt import QAction, QMenu, QKeySequence

    from . import hook
    from . import ui
    from . import config

    # Remove all related actions
    def remove_old_actions():
        menus_to_check = [mw.form.menuTools]
        for menu in menus_to_check:
            actions_to_remove = []
            for action in menu.actions():
                if action.text() in ['Adjust Sound Volume...', 'Toggle Mute', 'Sound Volume Settings']:
                    actions_to_remove.append(action)
                if action.menu():
                    sub_actions = action.menu().actions()
                    for sub_action in sub_actions:
                        if sub_action.text() in ['Toggle Mute', 'Sound Volume Settings']:
                            action.menu().removeAction(sub_action)
            for action in actions_to_remove:
                menu.removeAction(action)

    remove_old_actions()

    gui_hooks.av_player_did_begin_playing.append(hook.did_begin_playing)

    # Create submenu
    sound_menu = QMenu('Adjust Sound Volume', mw)
    mw.form.menuTools.addMenu(sound_menu)

    # Add volume settings action (at the top)
    volume_action = QAction('Volume Settings...', mw)
    volume_action.triggered.connect(lambda: ui.VolumeDialog(mw).show())
    volume_action.setShortcut(QKeySequence(config.load_config().settings_shortcut))
    sound_menu.addAction(volume_action)

    # Add separator
    sound_menu.addSeparator()

    # Add volume up action
    volume_up_action = QAction('Volume Up', mw)
    volume_up_action.triggered.connect(lambda: ui.adjust_volume(10))
    volume_up_action.setShortcut(QKeySequence(config.load_config().volume_up_shortcut))
    sound_menu.addAction(volume_up_action)

    # Add volume down action
    volume_down_action = QAction('Volume Down', mw)
    volume_down_action.triggered.connect(lambda: ui.adjust_volume(-10))
    volume_down_action.setShortcut(QKeySequence(config.load_config().volume_down_shortcut))
    sound_menu.addAction(volume_down_action)

    # Add mute toggle action
    mute_action = QAction('Toggle Mute', mw)
    mute_action.triggered.connect(ui.toggle_mute)
    mute_action.setShortcut(QKeySequence(config.load_config().mute_shortcut))
    sound_menu.addAction(mute_action)

    # Set shortcuts
    ui.setup_shortcuts()
