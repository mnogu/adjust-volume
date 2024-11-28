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
Defines the sound configuration UI.
"""

if __name__ == "__main__":
    pass
else:
    import sys
    from dataclasses import asdict
    from typing import Tuple

    from aqt import gui_hooks
    from aqt import mw
    from aqt.qt import (
        QCheckBox, QDialog, QDialogButtonBox, QGridLayout, QGroupBox,
        QHBoxLayout, QLabel, QMessageBox, QSizePolicy, QSlider,
        QSpinBox, QVBoxLayout, QWidget, Qt, QShortcut, QKeySequence,
        QKeySequenceEdit, QAction, QPushButton, QMainWindow
    )
    from aqt.sound import MpvManager
    from aqt.sound import av_player
    from aqt.utils import tooltip

    from . import config
    from . import hook
    
    def save_config(volume_config: config.VolumeConfig) -> None:
        """Save the sound volume configuration."""
        # No longer automatically set default shortcuts
        mw.addonManager.writeConfig(__name__, asdict(volume_config))

        gui_hooks.av_player_did_begin_playing.remove(hook.did_begin_playing)
        gui_hooks.av_player_did_begin_playing.append(hook.did_begin_playing)
        
        # Reset shortcuts
        setup_shortcuts()


    def _create_config_widgets(text: str, min_max: Tuple[int, int]) \
            -> Tuple[QLabel, QSlider, QSpinBox]:
        label = QLabel()
        label.setText(text)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        slider = QSlider()
        slider.setOrientation(Qt.Orientation.Horizontal)
        slider.setMinimum(min_max[0])
        slider.setMaximum(min_max[1])

        spin_box = QSpinBox()
        spin_box.setMinimum(min_max[0])
        spin_box.setMaximum(min_max[1])

        slider.valueChanged.connect(spin_box.setValue)
        spin_box.valueChanged.connect(slider.setValue)

        return label, slider, spin_box


    def _set_value(value: int, slider: QSlider, spin_box: QSpinBox) -> None:
        for widget in [slider, spin_box]:
            widget.setValue(value)


    def adjust_volume(delta: int):
        """Adjust the volume level"""
        volume_config = config.load_config()
        max_volume = 200 if volume_config.allow_volume_boost else 100
        new_volume = max(0, min(max_volume, volume_config.volume + delta))
        
        # Set to mute if volume is 0
        if new_volume == 0:
            volume_config.is_muted = True
        # Unmute if increasing volume from 0
        elif volume_config.volume == 0 and new_volume > 0:
            volume_config.is_muted = False
        # Unmute if increasing volume from muted state
        elif delta > 0 and volume_config.is_muted:
            volume_config.is_muted = False
        
        volume_config.volume = new_volume
        save_config(volume_config)
        
        # Show volume status
        status = "Muted" if volume_config.is_muted else f"Volume: {new_volume}%"
        tooltip(status)


    class VolumeDialog(QDialog):
        """A dialog window to set the sound volume"""

        def __init__(self, parent: QWidget) -> None:
            super().__init__(parent)

            # Volume control section
            volume_label, self.volume_slider, self.volume_spin_box = _create_config_widgets(
                'Volume', (0, 100))

            volume_layout = QGridLayout()  # Use QGridLayout for better alignment
            volume_layout.addWidget(volume_label, 0, 0)
            volume_layout.addWidget(self.volume_slider, 0, 1)
            volume_layout.addWidget(self.volume_spin_box, 0, 2)
            
            # Mute checkbox on a separate line
            self.mute_check_box = QCheckBox("Mute")
            volume_layout.addWidget(self.mute_check_box, 1, 0, 1, 3)
            
            self.mute_check_box.stateChanged.connect(self.on_mute_changed_silent)
            self.mute_check_box.stateChanged.connect(self.update_volume_controls)

            volume_group_box = QGroupBox("Volume Control")  # More clear title
            volume_group_box.setLayout(volume_layout)

            i_label, self.i_slider, self.i_spin_box = _create_config_widgets(
                'Integrated loudness', (-70, -5))
            self.dual_mono_check_box = QCheckBox(
                'Treat mono input as dual-mono')

            loudnorm_layout = QGridLayout()
            loudnorm_layout.addWidget(i_label, 0, 0)
            loudnorm_layout.addWidget(self.i_slider, 0, 1)
            loudnorm_layout.addWidget(self.i_spin_box, 0, 2)
            loudnorm_layout.addWidget(self.dual_mono_check_box, 1, 0, 1, 3)

            self.loudnorm_group_box = QGroupBox()
            self.loudnorm_group_box.setLayout(loudnorm_layout)
            self.loudnorm_group_box.setCheckable(True)
            self.loudnorm_group_box.setTitle(
                'Loudness Normalization (mpv only)')
            self.loudnorm_group_box.toggled.connect(self._show_warning_on_non_mpv)

            # Shortcut settings section
            shortcuts_layout = QGridLayout()
            
            shortcuts_title = QLabel("Keyboard Shortcuts")
            shortcuts_title.setStyleSheet("font-weight: bold;")
            shortcuts_layout.addWidget(shortcuts_title, 0, 0, 1, 2)
            
            general_tip = QLabel("Click to record, press Esc to clear")
            general_tip.setStyleSheet("color: gray; font-size: 10px;")
            shortcuts_layout.addWidget(general_tip, 0, 2)
            
            # Add volume adjustment shortcut settings
            shortcuts_layout.addWidget(QLabel("Volume Up:"), 1, 0)
            self.volume_up_shortcut_edit = QKeySequenceEdit()
            shortcuts_layout.addWidget(self.volume_up_shortcut_edit, 1, 1, 1, 2)

            shortcuts_layout.addWidget(QLabel("Volume Down:"), 2, 0)
            self.volume_down_shortcut_edit = QKeySequenceEdit()
            shortcuts_layout.addWidget(self.volume_down_shortcut_edit, 2, 1, 1, 2)

            shortcuts_layout.addWidget(QLabel("Mute:"), 3, 0)
            self.mute_shortcut_edit = QKeySequenceEdit()
            shortcuts_layout.addWidget(self.mute_shortcut_edit, 3, 1, 1, 2)

            shortcuts_layout.addWidget(QLabel("Settings:"), 4, 0)
            self.settings_shortcut_edit = QKeySequenceEdit()
            shortcuts_layout.addWidget(self.settings_shortcut_edit, 4, 1, 1, 2)
            
            reset_button = QPushButton("Reset Shortcuts")
            reset_button.clicked.connect(self.reset_shortcuts)
            shortcuts_layout.addWidget(reset_button, 5, 0, 1, 3)

            shortcuts_group = QGroupBox()
            shortcuts_group.setLayout(shortcuts_layout)

            # Main layout
            layout = QVBoxLayout()
            layout.addWidget(volume_group_box)
            layout.addWidget(self.loudnorm_group_box)
            layout.addWidget(shortcuts_group)
            layout.addStretch()
            
            # Button box
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            layout.addWidget(button_box)

            self.setWindowTitle('Sound Volume Settings')  # More clear window title
            self.setModal(True)
            self.setLayout(layout)
            
            # Set ESC key behavior for all shortcut editors
            for editor in [self.volume_up_shortcut_edit, 
                          self.volume_down_shortcut_edit,
                          self.mute_shortcut_edit,
                          self.settings_shortcut_edit]:
                editor.installEventFilter(self)

            # Connect volume change signals
            self.volume_slider.valueChanged.connect(self.on_volume_changed)
            self.volume_spin_box.valueChanged.connect(self.on_volume_changed)
            
            # Connect mute checkbox signal
            self.mute_check_box.stateChanged.connect(self.on_mute_changed)

            # Add volume boost checkbox
            self.volume_boost_check_box = QCheckBox("Allow volume boost up to 200%")
            volume_layout.addWidget(self.volume_boost_check_box, 2, 0, 1, 3)
            
            # Connect signals
            self.volume_boost_check_box.stateChanged.connect(self.on_volume_boost_changed)

        def _show_warning_on_non_mpv(self, checked: bool) -> None:
            if not checked:
                return

            if any(isinstance(player, MpvManager) for player in av_player.players):
                return

            QMessageBox.warning(self, 'mpv not found or too old',
                                'You need to install or update mpv and restart Anki '
                                'to use the loudness normalization feature.')

        def reset_shortcuts(self):
            """Reset shortcuts to default values"""
            self.volume_up_shortcut_edit.setKeySequence(QKeySequence("Ctrl+Alt+Up"))
            self.volume_down_shortcut_edit.setKeySequence(QKeySequence("Ctrl+Alt+Down"))
            self.mute_shortcut_edit.setKeySequence(QKeySequence("Ctrl+Alt+M"))
            self.settings_shortcut_edit.setKeySequence(QKeySequence("Ctrl+Alt+V"))
            
        def on_mute_changed_silent(self, state):
            """Handle mute state change without showing tooltip"""
            volume_config = config.load_config()
            volume_config.is_muted = bool(state)
            save_config(volume_config)
        
        def show(self) -> None:
            """Show the dialog window and its widgets."""
            volume_config = config.load_config()
            
            _set_value(volume_config.volume,
                       self.volume_slider, self.volume_spin_box)

            # Set mute state and update control states
            self.mute_check_box.setChecked(volume_config.is_muted)
            self.update_volume_controls(volume_config.is_muted)

            loudnorm = volume_config.loudnorm
            self.loudnorm_group_box.setChecked(loudnorm.enabled)
            _set_value(loudnorm.i, self.i_slider, self.i_spin_box)
            self.dual_mono_check_box.setChecked(loudnorm.dual_mono)
            
            # Set shortcuts, only set when there are values in the configuration
            if volume_config.volume_up_shortcut and volume_config.volume_up_shortcut.strip():
                self.volume_up_shortcut_edit.setKeySequence(QKeySequence(volume_config.volume_up_shortcut))
            else:
                self.volume_up_shortcut_edit.clear()
            
            if volume_config.volume_down_shortcut and volume_config.volume_down_shortcut.strip():
                self.volume_down_shortcut_edit.setKeySequence(QKeySequence(volume_config.volume_down_shortcut))
            else:
                self.volume_down_shortcut_edit.clear()

            if volume_config.mute_shortcut and volume_config.mute_shortcut.strip():
                self.mute_shortcut_edit.setKeySequence(QKeySequence(volume_config.mute_shortcut))
            else:
                self.mute_shortcut_edit.clear()
            
            if volume_config.settings_shortcut and volume_config.settings_shortcut.strip():
                self.settings_shortcut_edit.setKeySequence(QKeySequence(volume_config.settings_shortcut))
            else:
                self.settings_shortcut_edit.clear()

            # Set volume boost checkbox state
            self.volume_boost_check_box.setChecked(volume_config.allow_volume_boost)
            
            # Set maximum based on whether volume boost is allowed
            max_volume = 200 if volume_config.allow_volume_boost else 100
            self.volume_slider.setMaximum(max_volume)
            self.volume_spin_box.setMaximum(max_volume)

            super().show()

        def accept(self) -> None:
            """Save the sound volume and hide the dialog window."""
            volume_config = config.VolumeConfig()
            volume_config.volume = self.volume_slider.value()
            volume_config.is_muted = self.mute_check_box.isChecked()
            volume_config.loudnorm.enabled = self.loudnorm_group_box.isChecked()
            volume_config.loudnorm.i = self.i_slider.value()
            volume_config.loudnorm.dual_mono = self.dual_mono_check_box.isChecked()
            
            # Save volume boost setting
            volume_config.allow_volume_boost = self.volume_boost_check_box.isChecked()
            
            # Save volume adjustment shortcuts
            volume_up_seq = self.volume_up_shortcut_edit.keySequence()
            volume_down_seq = self.volume_down_shortcut_edit.keySequence()
            mute_seq = self.mute_shortcut_edit.keySequence()
            settings_seq = self.settings_shortcut_edit.keySequence()
            
            # Only save non-empty shortcuts
            volume_config.volume_up_shortcut = volume_up_seq.toString() if not volume_up_seq.isEmpty() else ""
            volume_config.volume_down_shortcut = volume_down_seq.toString() if not volume_down_seq.isEmpty() else ""
            volume_config.mute_shortcut = mute_seq.toString() if not mute_seq.isEmpty() else ""
            volume_config.settings_shortcut = settings_seq.toString() if not settings_seq.isEmpty() else ""
            
            # Save config first
            save_config(volume_config)
            
            # Force immediate shortcut update
            setup_shortcuts()
            
            # Force process events to ensure shortcuts are updated
            from aqt.qt import QApplication
            QApplication.instance().processEvents()
            
            super().accept()

        def eventFilter(self, obj, event) -> bool:
            """Handle ESC key press before it's recorded as a shortcut"""
            if (event.type() == event.Type.KeyPress and 
                event.key() == Qt.Key.Key_Escape and 
                isinstance(obj, QKeySequenceEdit)):
                obj.clear()
                return True  # Prevent ESC from being recorded
            return super().eventFilter(obj, event)

        def update_volume_controls(self, state):
            """Update volume control enabled states based on mute status and volume level"""
            is_muted = bool(state)
            volume = self.volume_slider.value()
            
            # Volume controls should always be enabled except when manually muted
            self.volume_slider.setEnabled(not is_muted or volume == 0)
            self.volume_spin_box.setEnabled(not is_muted or volume == 0)
            
            # Handle mute checkbox state
            if volume == 0:
                self.mute_check_box.setEnabled(False)
                self.mute_check_box.setChecked(True)
            else:
                self.mute_check_box.setEnabled(True)

        def on_volume_changed(self, value):
            """Handle volume change events"""
            if value > 0:
                # Enable mute checkbox and uncheck it
                self.mute_check_box.setEnabled(True)
                self.mute_check_box.setChecked(False)
                # Enable volume controls
                self.volume_slider.setEnabled(True)
                self.volume_spin_box.setEnabled(True)
            else:
                # Disable and check mute checkbox
                self.mute_check_box.setEnabled(False)
                self.mute_check_box.setChecked(True)
                # Keep volume controls enabled at 0
                self.volume_slider.setEnabled(True)
                self.volume_spin_box.setEnabled(True)

        def on_mute_changed(self, state):
            """Handle mute state changes"""
            is_muted = bool(state)
            volume = self.volume_slider.value()
            
            # Only disable volume controls when manually muted and volume > 0
            if volume > 0:
                self.volume_slider.setEnabled(not is_muted)
                self.volume_spin_box.setEnabled(not is_muted)

        def on_volume_boost_changed(self, state):
            """Handle volume boost checkbox state change"""
            allow_boost = bool(state)
            current_volume = self.volume_slider.value()
            
            # Update volume slider and spinbox range
            max_volume = 200 if allow_boost else 100
            self.volume_slider.setMaximum(max_volume)
            self.volume_spin_box.setMaximum(max_volume)
            
            # If boost is disabled and current volume > 100%, limit it to 100%
            if not allow_boost and current_volume > 100:
                self.volume_slider.setValue(100)
                self.volume_spin_box.setValue(100)


    def toggle_mute():
        """Toggle mute state only if volume is not 0"""
        volume_config = config.load_config()
        
        # Only toggle mute if volume is greater than 0
        if volume_config.volume > 0:
            volume_config.is_muted = not volume_config.is_muted
            save_config(volume_config)
            tooltip("Sound " + ("Muted" if volume_config.is_muted else "Unmuted"))
        else:
            tooltip("Cannot toggle mute when volume is 0")

    def setup_shortcuts():
        """Setup global shortcuts for volume control"""
        volume_config = config.load_config()
        
        # Clear existing shortcuts first
        if hasattr(mw, '_volume_shortcuts'):
            for action in mw._volume_shortcuts:
                # Explicitly disable and remove the shortcut before removing the action
                action.setShortcut(QKeySequence(""))
                action.setEnabled(False)
                mw.removeAction(action)
                action.deleteLater()
            
            # Clear the list
            mw._volume_shortcuts = []
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Force process pending events
            from aqt.qt import QApplication
            QApplication.instance().processEvents()
        
        def register_shortcut(key, fn):
            if not key or key.isspace():  # Skip if shortcut is empty or whitespace
                return None
            action = QAction(mw)
            action.setShortcut(QKeySequence(key))
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
            action.triggered.connect(fn)
            mw.addAction(action)
            return action
        
        # Initialize new shortcuts list if not exists
        if not hasattr(mw, '_volume_shortcuts'):
            mw._volume_shortcuts = []
        
        # Register new shortcuts
        shortcuts = [
            (volume_config.volume_up_shortcut, lambda: adjust_volume(10)),
            (volume_config.volume_down_shortcut, lambda: adjust_volume(-10)),
            (volume_config.mute_shortcut, toggle_mute),
            (volume_config.settings_shortcut, lambda: VolumeDialog(mw).show())
        ]
        
        for shortcut, callback in shortcuts:
            if action := register_shortcut(shortcut, callback):
                mw._volume_shortcuts.append(action)
        
        # Force update main window
        mw.update()
