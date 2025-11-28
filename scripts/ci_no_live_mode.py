"""CI guard: ensure that FINBOT_MODE=live is not enabled in build without explicit confirmation.

This script exits with a non-zero code if .env or env variables specify FINBOT_MODE=live
and FINBOT_LIVE_TRADING_CONFIRM=false or not set. It's intended to be run in CI before builds to
prevent accidental enabling of live trading.

Usage: python scripts/ci_no_live_mode.py
"""
import os
from pathlib import Path

def read_env_file(env_path: Path) -> dict:
    env = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()
    return env


def main():
    # Priority: actual env > .env file
    finbot_mode = os.getenv('FINBOT_MODE')
    confirm = os.getenv('FINBOT_LIVE_TRADING_CONFIRM')

    if not finbot_mode:
        env_file = Path('.env')
        env = read_env_file(env_file)
        finbot_mode = env.get('FINBOT_MODE')
        confirm = env.get('FINBOT_LIVE_TRADING_CONFIRM')

    if (finbot_mode or '').lower() == 'live':
        if (confirm or '').lower() != 'true':
            print('CI Guard: FINBOT_MODE=live without confirmation; aborting build.')
            print('Set FINBOT_LIVE_TRADING_CONFIRM=true only in approved release processes.')
            raise SystemExit(1)
        else:
            print('CI Guard: live mode explicitly confirmed.')
    else:
        print('CI Guard: FINBOT_MODE not set to live.')


if __name__ == '__main__':
    main()
