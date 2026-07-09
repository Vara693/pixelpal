import os

import pytest

from pixelpal.core.config_store import (
    ConfigStore,
    WindowState,
    load_window_state,
    save_window_state,
)


@pytest.fixture
def temp_config_path(tmp_path):
    return os.path.join(tmp_path, "config.ini")


def test_defaults_are_populated(temp_config_path):
    store = ConfigStore(path=temp_config_path)
    assert store.get_int("window", "pos_x") == 100
    assert store.get("window", "character") == "cat"
    assert store.get_bool("mood", "cpu_signal") is True


def test_set_and_save_persists_to_disk(temp_config_path):
    store = ConfigStore(path=temp_config_path)
    store.set_and_save("window", "pos_x", 250)

    assert os.path.isfile(temp_config_path)

    reloaded = ConfigStore(path=temp_config_path)
    assert reloaded.get_int("window", "pos_x") == 250


def test_set_without_save_does_not_persist(temp_config_path):
    store = ConfigStore(path=temp_config_path)
    store.set("window", "pos_x", 999)
    assert not os.path.isfile(temp_config_path)


def test_get_bool_parses_various_true_values(temp_config_path):
    store = ConfigStore(path=temp_config_path)
    store.set("mood", "git_watch_signal", "yes")
    assert store.get_bool("mood", "git_watch_signal") is True


def test_fallback_used_for_missing_key(temp_config_path):
    store = ConfigStore(path=temp_config_path)
    assert store.get("nonexistent_section", "missing_key", fallback="default") == "default"


def test_window_state_round_trip(temp_config_path):
    store = ConfigStore(path=temp_config_path)
    state = WindowState(pos_x=42, pos_y=84, character="fox")
    save_window_state(store, state)

    reloaded_store = ConfigStore(path=temp_config_path)
    reloaded_state = load_window_state(reloaded_store)

    assert reloaded_state.pos_x == 42
    assert reloaded_state.pos_y == 84
    assert reloaded_state.character == "fox"


def test_new_section_can_be_created_via_set(temp_config_path):
    store = ConfigStore(path=temp_config_path)
    store.set_and_save("custom_section", "custom_key", "custom_value")

    reloaded = ConfigStore(path=temp_config_path)
    assert reloaded.get("custom_section", "custom_key") == "custom_value"
