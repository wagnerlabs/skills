# Fusion Second Opinion

This skill asks OpenRouter Fusion for a blocking second opinion on non-trivial RCA, plans, implementations, documents, or analysis. It runs Codex in a read-only repository sandbox and sends the result through a panel of models synthesized by Claude Opus 4.8.

Fusion can combine multiple frontier models in a way that can potentially meet or exceed Fable 5 levels of intelligence; see OpenRouter's announcement, [Fusion beats frontier](https://openrouter.ai/blog/announcements/fusion-beats-frontier/).

## Levels

For comparison, OpenRouter measured Claude Fable 5 alone at 65.3% on DRACO.

| Level | Panel | DRACO score |
|---|---|---|
| `xhigh` | Opus 4.8 + GPT-5.5 + Gemini 3.1 Pro + DeepSeek V4 Pro, synthesized by Opus 4.8 | Untested |
| `high` (default) | Opus 4.8 + GPT-5.5 + Gemini 3.1 Pro, synthesized by Opus 4.8 | 68.3% |
| `medium` | Gemini 3 Flash + Kimi K2.6 + DeepSeek V4 Pro, synthesized by Opus 4.8 | 64.7% |

## API Keys

By default, the skill uses `OPENROUTER_API_KEY`, either from the current environment or from `${XDG_CONFIG_HOME:-$HOME/.config}/openrouter/credentials.env`.

If you use more than one OpenRouter key, define named keys in that credentials file:

```sh
OPENROUTER_API_KEY=sk-or-default...
OPENROUTER_API_KEY_WORK=sk-or-work...
OPENROUTER_API_KEY_PERSONAL=sk-or-personal...
```

Then select one when invoking the skill:

```sh
/fusion-second-opinion key:work
/fusion-second-opinion xhigh key:personal
/fusion-second-opinion env:OPENROUTER_API_KEY_WORK
```

`key:<name>` resolves to `OPENROUTER_API_KEY_<NAME>` after uppercasing the name. `env:<VAR>` uses exactly the environment variable named by `<VAR>`. Do not pass literal API keys as arguments; store them in the environment or credentials file instead.

`SKILL.md` contains the agent-facing invocation workflow and is the canonical skill definition.
