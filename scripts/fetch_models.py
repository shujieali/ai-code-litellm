#!/usr/bin/env python3
"""
Fetch available GitHub Copilot models and generate models.yaml

This script:
1. Authenticates with GitHub Copilot (if needed)
2. Fetches all available chat models
3. Generates models.yaml with proper LiteLLM format

Usage:
  python3 scripts/fetch_models.py
  python3 scripts/fetch_models.py --output models.yaml
"""
import argparse
import json
import sys
import subprocess
from pathlib import Path

GITHUB_TOKEN_FILE = Path.home() / ".config/litellm/github_copilot/access-token"


def get_github_token():
    """Get GitHub Copilot access token, prompt for auth if needed."""
    if not GITHUB_TOKEN_FILE.exists():
        print("❌ GitHub Copilot token not found")
        print(f"   Expected at: {GITHUB_TOKEN_FILE}")
        print("")
        print("To authenticate:")
        print("  1. Run LiteLLM with GitHub Copilot model once to trigger auth:")
        print("     litellm --model github_copilot/gpt-4o --test")
        print("  2. Or authenticate manually via GitHub CLI")
        return None

    return GITHUB_TOKEN_FILE.read_text().strip()


def fetch_copilot_models(token):
    """Fetch available models from GitHub Copilot API."""
    import urllib.request
    import urllib.error

    headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request("https://api.githubcopilot.com/models", headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to fetch models: {e.code}")
        print(e.read().decode())
        return None
    except Exception as e:
        print(f"❌ Error fetching models: {e}")
        return None

    # Filter for chat models only
    chat_models = [
        m for m in data.get("data", [])
        if m.get("capabilities", {}).get("type") == "chat"
    ]

    return chat_models


def generate_models_yaml(models, output_path):
    """Generate models.yaml from fetched models."""
    lines = ["model_list:"]

    for model in models:
        model_id = model["id"]
        model_name = model.get("name", model_id)
        vendor = model.get("vendor", "Unknown")
        state = model.get("policy", {}).get("state", "enabled") if model.get("policy") else "enabled"
        max_output = model.get("capabilities", {}).get("limits", {}).get("max_output_tokens", 4096)
        max_context = model.get("capabilities", {}).get("limits", {}).get("max_context_window_tokens", 128000)

        lines.append(f"  - model_name: {model_id}")
        lines.append(f"    litellm_params:")
        lines.append(f"      model: github_copilot/{model_id}")
        lines.append(f'      extra_headers: {{"Editor-Version": "vscode/1.85.1", "Copilot-Integration-Id": "vscode-chat"}}')

        # Add drop_params for Claude models
        if "claude" in model_id.lower():
            lines.append(f"      drop_params: true")

        lines.append(f"    # {model_name} ({vendor}) - {state}")
        lines.append(f"    # Max tokens: {max_output}, Context: {max_context}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Generated {len(models)} models in {output_path}")
    print(f"   Models: {', '.join([m['id'] for m in models[:5]])}...")


def main():
    p = argparse.ArgumentParser(description="Fetch GitHub Copilot models and generate models.yaml")
    p.add_argument("--output", default="models.yaml", help="Output YAML file path")
    p.add_argument("--enabled-only", action="store_true", help="Only fetch enabled models")
    args = p.parse_args()

    output_path = Path(args.output)

    # Get token
    token = get_github_token()
    if not token:
        sys.exit(1)

    print("Fetching GitHub Copilot models...")
    models = fetch_copilot_models(token)
    if not models:
        sys.exit(1)

    # Filter enabled only if requested
    if args.enabled_only:
        models = [
            m for m in models
            if not m.get("policy") or m.get("policy", {}).get("state") == "enabled"
        ]

    print(f"Found {len(models)} models")

    # Generate YAML
    generate_models_yaml(models, output_path)


if __name__ == "__main__":
    main()
