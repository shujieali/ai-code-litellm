#!/usr/bin/env python3
"""
Set or remove ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN in ~/.claude/settings.json (no state file, no backups).

Behavior:
- "set [URL]" will add/update two keys under the top-level "env" object in the Claude settings file:
    ANTHROPIC_BASE_URL -> URL (default: http://localhost:4000)
    ANTHROPIC_AUTH_TOKEN -> obtained from a .env file (see --env-path) or provided via --token

- "restore" will remove both ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN keys from the "env" object (if present).

- The script edits ~/.claude/settings.json in-place and preserves all other keys.
- It will abort if the existing "env" value is present but not a JSON object.

Compatibility:
- Accepts a --force flag for Makefile compatibility (no-op).
- Default .env path is the claude-code-over-github-copilot repo under the project root.

Usage examples:
  # set using the master key found in the claude repo .env
  python3 scripts/anthropic_endpoint.py set

  # set to custom URL and explicit token
  python3 scripts/anthropic_endpoint.py set http://localhost:4000 --token litellm-...

  # remove the two keys
  python3 scripts/anthropic_endpoint.py restore
"""
import argparse
import json
import sys
from pathlib import Path

# Defaults
DEFAULT_URL = "http://localhost:4000"
# Default path to .env (same directory as script parent)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"

CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"


def parse_dotenv(path: Path):
    """Parse a simple dotenv file into a dict. Returns empty dict on missing file."""
    res = {}
    if not path.exists():
        return res
    text = path.read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        res[k] = v
    return res


def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: Can't parse {path}: {e}")
        sys.exit(1)


def write_json(path: Path, obj: dict):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["set", "restore"])  # set or restore
    p.add_argument("url", nargs="?", default=DEFAULT_URL)
    p.add_argument("--token", help="Explicit token to set (overrides reading .env)")
    p.add_argument("--env-path", default=str(DEFAULT_ENV_PATH), help="Path to .env to read LITELLM_MASTER_KEY from")
    p.add_argument("--force", action="store_true", help="No-op (compatibility with Makefile)")
    args = p.parse_args()

    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    settings = read_json(SETTINGS_FILE)

    env = settings.get("env")
    if env is None:
        env = {}
    elif not isinstance(env, dict):
        print("ERROR: existing 'env' value is not a JSON object. Aborting to avoid data loss.")
        sys.exit(1)

    if args.action == "set":
        url = args.url

        # Determine token: priority -> --token arg -> .env LITELLM_MASTER_KEY -> env var LITELLM_MASTER_KEY
        token = None
        if args.token:
            token = args.token
        else:
            env_path = Path(args.env_path)
            if env_path.exists():
                dot = parse_dotenv(env_path)
                token = dot.get("LITELLM_MASTER_KEY") or dot.get("MASTER_KEY")
            if token is None:
                # try environment variable as a last resort
                token = (Path.cwd() / ".env").exists() and parse_dotenv(Path.cwd() / ".env").get("LITELLM_MASTER_KEY")
            if token is None:
                token = None

        if token is None:
            print("ERROR: No token found. Provide --token or ensure LITELLM_MASTER_KEY exists in the .env at the default path.")
            print(f"Tried: --token, {args.env_path}, and ./ .env")
            sys.exit(1)

        # Set only the two keys requested, preserve other env keys
        env.setdefault("ANTHROPIC_BASE_URL", url)
        env["ANTHROPIC_BASE_URL"] = url
        env.setdefault("ANTHROPIC_AUTH_TOKEN", token)
        env["ANTHROPIC_AUTH_TOKEN"] = token

        settings["env"] = env
        write_json(SETTINGS_FILE, settings)
        print(f"Set ANTHROPIC_BASE_URL -> {url}")
        print(f"Set ANTHROPIC_AUTH_TOKEN -> (hidden, length={len(token) if token else 0})")
        return

    # restore: remove both keys and the entire env object if it becomes empty
    modified = False
    if isinstance(settings.get("env"), dict):
        if "ANTHROPIC_BASE_URL" in settings["env"]:
            settings["env"].pop("ANTHROPIC_BASE_URL", None)
            modified = True
        if "ANTHROPIC_AUTH_TOKEN" in settings["env"]:
            settings["env"].pop("ANTHROPIC_AUTH_TOKEN", None)
            modified = True

        # Remove entire env object if it's now empty
        if not settings["env"]:
            settings.pop("env", None)
            print("Removed empty env object from settings.json")

    if modified:
        write_json(SETTINGS_FILE, settings)
        print("Removed ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN from settings.json")
    else:
        print("ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN not present; nothing to do.")


if __name__ == "__main__":
    main()
