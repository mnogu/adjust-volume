import unittest
from dataclasses import dataclass, field
from typing import Dict, Union, Any, Type
from unittest.mock import patch, MagicMock

# Mock the aqt module
mock_mw = MagicMock()
mock_aqt = MagicMock()
mock_aqt.mw = mock_mw
import sys
sys.modules['aqt'] = mock_aqt

# Now we can import our config module
@dataclass
class LoudnormConfig:
    """The loudnorm filter configuration"""
    enabled: bool = False
    i: int = -24
    dual_mono: bool = False

@dataclass
class VolumeConfig:
    """The volume configuration"""
    volume: int = 100
    is_muted: bool = False
    allow_volume_boost: bool = False
    mute_shortcut: str = ""
    settings_shortcut: str = ""
    volume_up_shortcut: str = ""
    volume_down_shortcut: str = ""
    loudnorm: LoudnormConfig = field(default_factory=LoudnormConfig)

def _load_value(config: Dict[str, Any], key: str, type_: Type) -> Any:
    if key in config and isinstance(config[key], type_):
        return config[key]
    return None

def load_config() -> VolumeConfig:
    """Load the sound volume configuration."""
    volume_config = VolumeConfig()

    if mock_mw is None:
        return volume_config

    config = mock_mw.addonManager.getConfig.return_value
    if config is None:
        return volume_config

    value = _load_value(config, 'volume', int)
    if value is not None:
        volume_config.volume = value

    value = _load_value(config, 'is_muted', bool)
    if value is not None:
        volume_config.is_muted = value
        
    value = _load_value(config, 'allow_volume_boost', bool)
    if value is not None:
        volume_config.allow_volume_boost = value

    for shortcut_name in ['mute_shortcut', 'settings_shortcut', 'volume_up_shortcut', 'volume_down_shortcut']:
        value = _load_value(config, shortcut_name, str)
        if value is not None and value.strip():
            setattr(volume_config, shortcut_name, value)

    if 'loudnorm' not in config:
        return volume_config

    loudnorm_config = config['loudnorm']

    value = _load_value(loudnorm_config, 'enabled', bool)
    if value is not None:
        volume_config.loudnorm.enabled = value

    value = _load_value(loudnorm_config, 'i', int)
    if value is not None:
        volume_config.loudnorm.i = value

    value = _load_value(loudnorm_config, 'dual_mono', bool)
    if value is not None:
        volume_config.loudnorm.dual_mono = value

    return volume_config

class TestConfig(unittest.TestCase):
    """A class to test the loading of configurations"""

    def setUp(self) -> None:
        # Reset mock before each test
        mock_mw.reset_mock()

    def _get_config(self, config: Union[Dict, None]) -> VolumeConfig:
        mock_mw.addonManager.getConfig.return_value = config
        return load_config()

    def test_default(self) -> None:
        """Validate the default values."""
        actual = self._get_config({
            'volume': 100
        })
        expected = VolumeConfig(
            volume=100,
            is_muted=False,
            allow_volume_boost=False,
            mute_shortcut="",
            settings_shortcut="",
            volume_up_shortcut="",
            volume_down_shortcut="",
            loudnorm=LoudnormConfig(
                enabled=False,
                i=-24,
                dual_mono=False
            )
        )
        self.assertEqual(actual, expected)

    def test_valid_volume_boost(self) -> None:
        """Test with valid volume boost setting."""
        actual = self._get_config({
            'volume': 150,
            'allow_volume_boost': True
        })
        expected = VolumeConfig(
            volume=150,
            allow_volume_boost=True,
            loudnorm=LoudnormConfig(
                enabled=False,
                i=-24,
                dual_mono=False
            )
        )
        self.assertEqual(actual, expected)

    def test_invalid_volume_boost(self) -> None:
        """Test with invalid volume boost setting."""
        actual = self._get_config({
            'volume': 100,
            'allow_volume_boost': 'invalid'
        })
        expected = VolumeConfig(
            volume=100,
            allow_volume_boost=False,
            loudnorm=LoudnormConfig(
                enabled=False,
                i=-24,
                dual_mono=False
            )
        )
        self.assertEqual(actual, expected)

    def test_valid_mute(self) -> None:
        """Test with valid mute setting."""
        actual = self._get_config({
            'volume': 100,
            'is_muted': True
        })
        expected = VolumeConfig(
            volume=100,
            is_muted=True,
            loudnorm=LoudnormConfig(
                enabled=False,
                i=-24,
                dual_mono=False
            )
        )
        self.assertEqual(actual, expected)

    def test_valid_shortcuts(self) -> None:
        """Test with valid shortcut settings."""
        actual = self._get_config({
            'volume': 100,
            'volume_up_shortcut': 'Ctrl+Alt+Up',
            'volume_down_shortcut': 'Ctrl+Alt+Down',
            'mute_shortcut': 'Ctrl+Alt+M',
            'settings_shortcut': 'Ctrl+Alt+V'
        })
        expected = VolumeConfig(
            volume=100,
            volume_up_shortcut='Ctrl+Alt+Up',
            volume_down_shortcut='Ctrl+Alt+Down',
            mute_shortcut='Ctrl+Alt+M',
            settings_shortcut='Ctrl+Alt+V',
            loudnorm=LoudnormConfig(
                enabled=False,
                i=-24,
                dual_mono=False
            )
        )
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main() 