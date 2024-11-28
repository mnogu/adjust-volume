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
Defines the hook to set the sound volume.
"""

if __name__ == "__main__":
    pass
else:
    from typing import Any

    from aqt.sound import MpvManager
    from aqt.sound import SimpleMplayerSlaveModePlayer

    from anki.sound import AVTag

    from . import config


def did_begin_playing(player: Any, _: AVTag) -> None:
    """Set the sound volume."""
    volume_config = config.load_config()
    actual_volume = 0 if volume_config.is_muted else volume_config.volume
    
    if isinstance(player, SimpleMplayerSlaveModePlayer):
        player.command('volume', actual_volume, '1')
    elif isinstance(player, MpvManager):
        player.set_property('volume', actual_volume)
        
        if volume_config.loudnorm.enabled:
            i = volume_config.loudnorm.i
            dual_mono = str(volume_config.loudnorm.dual_mono).lower()
            loudnorm_value = f'loudnorm=I={i}:dual_mono={dual_mono}'
        else:
            loudnorm_value = ''
        player.set_property('af', loudnorm_value)
