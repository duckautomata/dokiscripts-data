#!/usr/bin/env python3
"""Shared constants, regex, and config loading used across scripts."""

import os
import re
import sys
from typing import Any

import yaml

BASE_DIR = "Transcript"
CONFIG_FILE = "config.yaml"
CHANNELS_FILE = "channels.yaml"

# {YYYYMMDD} - {StreamType} - {StreamName} - [{id}].srt
FILENAME_PATTERN = re.compile(r"^(\d{8}) - (.+?) - (.+) - \[([^\]]+)\]\.srt$")


def load_config(require_api_key: bool = True) -> dict[str, Any]:
    """Load config.yaml. Exits on missing file or missing required keys."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)

    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error parsing '{CONFIG_FILE}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading '{CONFIG_FILE}': {e}")
        sys.exit(1)

    if not config:
        print(f"Error: '{CONFIG_FILE}' is empty.")
        sys.exit(1)

    if "server_url" not in config:
        print(f"Error: 'server_url' not found in '{CONFIG_FILE}'.")
        sys.exit(1)

    if require_api_key and "api_key" not in config:
        print(f"Error: 'api_key' not found in '{CONFIG_FILE}'.")
        sys.exit(1)

    return config


def load_channels() -> list[dict[str, Any]]:
    """Load channels.yaml with the list of channels and their download sources."""
    if not os.path.exists(CHANNELS_FILE):
        print(f"Error: Channels file '{CHANNELS_FILE}' not found.")
        sys.exit(1)

    try:
        with open(CHANNELS_FILE) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error parsing '{CHANNELS_FILE}': {e}")
        sys.exit(1)

    if not data or "channels" not in data:
        print(f"Error: '{CHANNELS_FILE}' is missing 'channels' list.")
        sys.exit(1)

    return data["channels"]
