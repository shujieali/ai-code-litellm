# AI Code LiteLLM Proxy

Configure AI coding assistants (Claude Code, Cursor, etc.) to use a local LiteLLM proxy instead of their default servers.

## Supported Tools

- ✅ **Claude Code** - Fully supported
- 🚧 **Cursor** - Coming soon
- 🚧 **GitHub Copilot Chat** - Coming soon
- 🚧 **Cody** - Coming soon

## Why?

- **Privacy**: Keep your code and conversations local
- **Cost Control**: Use models you already have access to
- **Flexibility**: Route requests through any LLM provider supported by LiteLLM
- **Compliance**: Meet company policies that restrict sending data to specific vendors
- **Multi-Provider**: Switch between OpenAI, Anthropic, Azure, local models, etc.

## What This Does

This project provides scripts to:
- Configure Claude Code to use a custom LiteLLM endpoint
- Dynamically fetch and update available models from GitHub Copilot
- Generate LiteLLM configuration files automatically
- Manage API tokens and authentication

**Important**: This project only configures Claude Code settings. You need to run LiteLLM proxy separately (via Docker or locally).

## Quick Start

### 1. Install Dependencies

```bash
git clone https://github.com/YOUR_USERNAME/claude-litellm-proxy.git
cd claude-litellm-proxy
```

No Python dependencies needed! Everything uses standard library except for optional model fetching.

### 2. Generate API Keys

```bash
make generate-env
```

Creates `.env` with:
- `LITELLM_MASTER_KEY` - API authentication token
- `LITELLM_SALT_KEY` - Salt key for LiteLLM
- Other LiteLLM settings

### 3. Fetch Models & Generate Config (Optional)

If you have GitHub Copilot access:

```bash
make update-config
```

This:
- Fetches all available GitHub Copilot models
- Generates `models.yaml` with model definitions
- Merges with `litellm_config_base.yaml` to create final `litellm_config.yaml`

### 4. Start LiteLLM Proxy

**Option A: Docker (Recommended)**

```bash
docker run -p 4000:4000 \
  -v $(pwd)/litellm_config.yaml:/app/config.yaml \
  -e LITELLM_MASTER_KEY=$(grep LITELLM_MASTER_KEY .env | cut -d '=' -f2) \
  ghcr.io/berriai/litellm:main-latest \
  --config /app/config.yaml --port 4000
```

**Option B: Local Install**

```bash
pip install litellm[proxy]
litellm --config litellm_config.yaml --port 4000
```

### 5. Configure Claude Code

```bash
make claude-set
```

This updates `~/.claude/settings.json` to point Claude Code to `http://localhost:4000`.

### 6. Use Claude Code

```bash
cd /your/project
claude
```

Claude Code now routes through your local LiteLLM proxy!

## Project Structure

```
claude-litellm-proxy/
├── Makefile                     # Quick commands
├── requirements.txt             # Python dependencies (minimal)
├── .env                         # Generated API keys (git-ignored)
├── litellm_config_base.yaml     # Base LiteLLM config (edit this)
├── models.yaml                  # Generated models list (auto-generated)
├── litellm_config.yaml          # Final merged config (auto-generated)
└── scripts/
    ├── anthropic_endpoint.py    # Configure Claude settings
    ├── generate_env.py          # Generate .env file
    ├── fetch_models.py          # Fetch GitHub Copilot models
    ├── merge_config.py          # Merge base + models config
    └── list-copilot-models.sh   # List available models
```

## Available Commands

```bash
make help              # Show all commands
make generate-env      # Generate .env with API keys
make fetch-models      # Fetch GitHub Copilot models → models.yaml
make merge-config      # Merge base config + models → litellm_config.yaml
make update-config     # Fetch models + merge (one command)
make list-models       # List available GitHub Copilot models
make claude-set        # Configure Claude to use proxy
make claude-restore    # Restore Claude to default (remove proxy config)
```

## Configuration

### Dynamic Model List

The model list is fetched dynamically from GitHub Copilot:

1. **Edit base config**: `litellm_config_base.yaml` (Redis, database, general settings)
2. **Fetch models**: `make fetch-models` (creates `models.yaml`)
3. **Merge config**: `make merge-config` (creates final `litellm_config.yaml`)
4. **Or use**: `make update-config` (does steps 2+3 automatically)

### Custom Endpoint

Use a different port or URL:

```bash
python3 scripts/anthropic_endpoint.py set http://localhost:8080
```

### Custom Token

```bash
python3 scripts/anthropic_endpoint.py set http://localhost:4000 --token your-token
```

### Restore Original Settings

```bash
make claude-restore
```

Removes proxy configuration from Claude Code settings.

## How It Works

### Configuration Script

The `anthropic_endpoint.py` script:
1. Reads your existing `~/.claude/settings.json`
2. Updates **only** `env.ANTHROPIC_BASE_URL` and `env.ANTHROPIC_AUTH_TOKEN`
3. Preserves all other settings (plugins, statusLine, etc.)
4. Writes back in-place (no backups created)

### Restore

The restore command:
1. Removes `ANTHROPIC_BASE_URL` from settings
2. Removes `ANTHROPIC_AUTH_TOKEN` from settings
3. Removes the entire `env` object if it's now empty
4. Claude Code reverts to default Anthropic servers

## LiteLLM Setup

### With GitHub Copilot

You need a GitHub Copilot account to use GitHub Copilot models. Authenticate on first use:

```bash
# LiteLLM will prompt for GitHub device authentication
litellm --model github_copilot/gpt-4o --test
```

Token is saved to `~/.config/litellm/github_copilot/access-token`.

### With Other Providers

Edit `litellm_config_base.yaml` and change model configurations to use:
- OpenAI
- Anthropic (direct)
- Azure OpenAI
- Any provider supported by LiteLLM

See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for all options.

## Troubleshooting

### Claude Code not using proxy

1. **Check settings**:
   ```bash
   cat ~/.claude/settings.json
   ```
   Should contain:
   ```json
   {
     "env": {
       "ANTHROPIC_BASE_URL": "http://localhost:4000",
       "ANTHROPIC_AUTH_TOKEN": "litellm-..."
     }
   }
   ```

2. **Verify proxy is running**:
   ```bash
   curl http://localhost:4000/health
   ```

3. **Check LiteLLM logs** for errors

### Token not found error

Generate `.env`:
```bash
make generate-env
```

Or provide token manually:
```bash
python3 scripts/anthropic_endpoint.py set --token litellm-your-key
```

### GitHub Copilot authentication

If model fetching fails with authentication error:

```bash
# Authenticate with GitHub Copilot
litellm --model github_copilot/gpt-4o --test
```

Follow the device authentication prompts.

### Model not found errors

LiteLLM is trying to use a model that doesn't exist or isn't healthy:

1. **Refresh models**:
   ```bash
   make update-config
   ```

2. **Check available models**:
   ```bash
   make list-models
   ```

3. **Verify model exists** in LiteLLM UI or logs

## Security

- **`.env` contains sensitive API keys** - never commit to version control
- **`.gitignore` protects** `.env`, `litellm_config.yaml`, and `models.yaml`
- **All requests stay local** (`localhost:4000`) - no external traffic to Anthropic
- **Token authentication** required for LiteLLM proxy access

## What This Does NOT Do

- ❌ Run the LiteLLM proxy server (you need Docker or local install)
- ❌ Provide GitHub Copilot access (requires GitHub subscription)
- ❌ Create backups of Claude settings (edits in-place)
- ❌ Modify any Claude settings other than `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`

## Requirements

- Python 3.x (standard library only for core functionality)
- Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
- LiteLLM proxy running (Docker or local)
- GitHub Copilot account (if using GitHub Copilot models)

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.

## Related Projects

- [LiteLLM](https://github.com/BerriAI/litellm) - The proxy server this project configures
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) - Anthropic's CLI tool
- [GitHub Copilot](https://github.com/features/copilot) - Model provider

## Acknowledgments

This project is a simple configuration wrapper around:
- **LiteLLM** by BerriAI for the amazing proxy server
- **Claude Code** by Anthropic for the CLI tool
- **GitHub Copilot** for model access
