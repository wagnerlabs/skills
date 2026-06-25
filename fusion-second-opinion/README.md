# Fusion Second Opinion

This skill asks OpenRouter Fusion for a blocking second opinion on non-trivial RCA, plans, implementations, documents, or analysis. It runs Codex in a read-only repository sandbox and sends the result through a panel of models synthesized by Claude Opus 4.8.

Fusion can combine multiple frontier models in a way that can potentially meet or exceed Fable 5 levels of intelligence; see OpenRouter's announcement, [Fusion beats frontier](https://openrouter.ai/blog/announcements/fusion-beats-frontier/).

## Levels

For comparison, OpenRouter measured Claude Fable 5 alone at 65.3% on DRACO.

| Level | Panel | DRACO score |
|---|---|---|
| `medium` | Gemini 3 Flash + Kimi K2.6 + DeepSeek V4 Pro, synthesized by Opus 4.8 | 64.7% |
| `high` (default) | Opus 4.8 + GPT-5.5 + Gemini 3.1 Pro, synthesized by Opus 4.8 | 68.3% |
| `xhigh` | Opus 4.8 + GPT-5.5 + Gemini 3.1 Pro + DeepSeek V4 Pro, synthesized by Opus 4.8 | Untested |

`SKILL.md` contains the agent-facing invocation workflow and is the canonical skill definition.
