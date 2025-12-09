#!/usr/bin/env python3
"""Validate environment configuration files against the settings schema."""

import sys
from pathlib import Path

from backend.app.config import Settings


def validate_env_file(env_file: str) -> bool:
    """Validate a specific .env file against the Settings schema."""
    env_path = Path(env_file)
    if not env_path.exists():
        print(f"❌ {env_file} does not exist")
        return False

    try:
        # Load settings with the specific env file
        settings = Settings(_env_file=env_path)
        print(f"✅ {env_file} is valid")
        return True
    except Exception as e:
        print(f"❌ {env_file} validation failed: {e}")
        return False


def main():
    """Main validation function."""
    env_files = [".env.dev", ".env.paper", ".env.live"]
    all_valid = True

    print("🔍 Validating environment configuration files...\n")

    for env_file in env_files:
        if not validate_env_file(env_file):
            all_valid = False

    if all_valid:
        print("\n🎉 All environment files are valid!")
        sys.exit(0)
    else:
        print("\n💥 Some environment files are invalid!")
        sys.exit(1)


if __name__ == "__main__":
    main()
