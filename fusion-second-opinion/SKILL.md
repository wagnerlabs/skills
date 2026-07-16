---
name: fusion-second-opinion
description: "Sends a time-expensive, blocking review packet to OpenRouter Fusion via Codex CLI in a read-only sandbox, using selectable medium/high/xhigh model panels and optional OpenRouter API key selectors. Defaults to high: Opus 4.8, GPT-5.6-Sol (max effort), and Gemini 3.1 Pro synthesized by Opus 4.8. Use when the user asks or when an agent judges that an independent multi-model second opinion would materially improve non-trivial RCA, plans, implementations, documents, or analysis responses; generally at most once per non-trivial task/artifact. Once invoked, the current task must pause until the intended review is verified as substantively complete and considered; repair and rerun a fixable incomplete pass, and do not continue after an unremediable one unless the user explicitly waives the review."
---

# Fusion second opinion

## Invocation policy

- Run this skill when the user explicitly asks.
- You may also use it, at your discretion, for non-trivial artifacts where an independent multi-model review would materially improve quality.
- This skill is time-expensive and optional by default. It is highly recommended after a non-trivial implementation plan is ready for review, before implementing.
- Once this skill is invoked for a task/artifact, it is **blocking for that task**: do not proceed with the fix, implementation, plan revision, document finalization, user-facing answer, or other reviewed work until the packet has been built and validated, Fusion has returned its output, you have verified that Fusion actually completed the intended review, you have read the full output, and you have decided which feedback to adopt.
- Do **not** run this skill in parallel while continuing the same workstream. It is acceptable to use a background process only to avoid tool timeouts, but you must wait for completion and consume the review output before advancing the task under review.
- If the intended second-opinion review cannot be completed after safe, in-scope remediation is exhausted, stop the reviewed work and report the failure to the user. Do not proceed unless a valid review later completes or the user explicitly tells you to continue without it.
- Default frequency: at most once per non-trivial task. You may run it once more for a materially different downstream artifact with important differences, such as an implementation that significantly diverged from the reviewed plan. Avoid reruns for minor edits, small follow-ups, or unchanged artifacts.

## Review completion gate

A finished subprocess is not necessarily a finished review. This gate closes the loophole where the command ran but the intended review did not; it does not expand an ordinary review beyond its requested scope or require rechecking incidental background. Before treating this skill as complete, verify all of the following:

- The Fusion command exited successfully and produced non-empty, substantive output with exactly one normalized `REVIEW STATUS: COMPLETE` marker and no `REVIEW STATUS: INCOMPLETE` marker within its first five non-empty lines.
- The proxy log proves that the configured Fusion plugin was injected and that the plugin-injected POST received a successful upstream response. A model's own claim that its panel ran is not sufficient execution evidence.
- The output identifies the concrete repository target and artifacts Fusion inspected and does not disclose any required item as uninspected.
- The output substantively addresses the entire requested scenario and scope. Fusion must have used the correct packet, transcript, repository or diff, and every referenced plan, implementation, document, analysis, or image needed for the review. For a two-phase scenario, both phases must be present.
- Fusion independently checks the code, analysis, and agent-supplied factual claims, test results, or conclusions that materially support the review target or verdict against primary evidence. The packet must identify those load-bearing items and their verification paths. User-stated premises remain user inputs unless the requested review expressly asks Fusion to verify them.
- If evidence, credentials, permissions, or tools needed for a material check are unavailable, the review is incomplete. A limitation affecting only a non-material point may be disclosed without invalidating an otherwise complete review, but Fusion must not use that unverified point to support its verdict.
- Neither the output nor the execution evidence reveals an authentication, credential, permission, tool, path, repository, context, panel-model, synthesis, or other model failure affecting the required scope. Treat a misunderstood packet or scenario, a skipped material target or required panel contribution, generic feedback that does not engage with the target, a partial review, or a stated inability to inspect a material or required item as incomplete even if the command exited zero or some useful feedback was returned.

Exactly one `REVIEW STATUS: COMPLETE` marker and no `REVIEW STATUS: INCOMPLETE` marker within the first five non-empty lines is necessary but not sufficient. Read the full output and relevant logs, then validate the review's substance before taking any post-review action. Your own inspection or verification cannot substitute for a missing part of Fusion's review.

If the completion gate fails:

1. If the cause can be corrected without user input or new authority, fix it and rerun the second-opinion review. This is required, not optional. Examples include repairing the packet or prompt, correcting a scenario or path, provisioning already-authorized read-only access, adding a complete raw export plus the exact query or analysis command, converting a validator to a write-free form, or preparing a faithful disposable review copy when a material check must write inside its checkout. Do not repeat an unchanged failing command. Validate the replacement output and logs against this gate. Attempts required to obtain the first valid review do not count as additional discretionary reviews under the default-frequency rule.
2. If Fusion reviewed only part of the intended scope or a required panel/synthesis step failed, treat the whole pass as incomplete. Repair and rerun it; do not fill the gap yourself and continue.
3. Only after safe, in-scope remediation is exhausted, if the review still cannot be completed as intended or the remaining remediation requires unavailable credentials, user input, new authority, or an external state change, **stop the task under review**. This is a pause for the user's decision, not permission to finish the work. Tell the user what failed, what was attempted, and what is needed, and provide the run-directory evidence when available. Do not implement, revise, finalize, or return the reviewed artifact as though the review occurred. Resume only after a valid review completes or the user explicitly directs you to proceed without it.

## Fusion levels

High is the default. To request a different level, invoke this skill with one level argument: `medium`, `high`, or `xhigh`.

| Level | Synthesizer | Analysis panel |
|---|---|---|
| `medium` | `anthropic/claude-opus-4.8` | `google/gemini-3-flash-preview`, `moonshotai/kimi-k2.6`, `deepseek/deepseek-v4-pro` |
| `high` (default) | `anthropic/claude-opus-4.8` | `anthropic/claude-opus-4.8`, `openai/gpt-5.6-sol` (max effort), `google/gemini-3.1-pro-preview` |
| `xhigh` | `anthropic/claude-opus-4.8` | `anthropic/claude-opus-4.8`, `openai/gpt-5.6-sol` (max effort), `google/gemini-3.1-pro-preview`, `deepseek/deepseek-v4-pro` |

## OpenRouter API key selection

Default behavior is unchanged: use `OPENROUTER_API_KEY`, either already exported or stored in `${XDG_CONFIG_HOME:-$HOME/.config}/openrouter/credentials.env`.

To select a different key, pass one key selector argument in addition to the optional level, in any order:

- `key:work` resolves to `OPENROUTER_API_KEY_WORK`.
- `key:personal` resolves to `OPENROUTER_API_KEY_PERSONAL`.
- `env:OPENROUTER_API_KEY_WORK` resolves to exactly `OPENROUTER_API_KEY_WORK`.

Never pass a literal API key as an argument. Store named keys as environment variables, for example:

```sh
OPENROUTER_API_KEY=sk-or-default...
OPENROUTER_API_KEY_WORK=sk-or-work...
OPENROUTER_API_KEY_PERSONAL=sk-or-personal...
```

Use one of these scenarios:

| Scenario | When | What Fusion does |
|---|---|---|
| `independent-rca` | After your own RCA, before fixing a bug | Performs its own independent RCA from scratch — does NOT see yours |
| `plan-review` | After drafting a feature plan, before implementing | Reviews and critiques the plan |
| `post-implementation-review` | After implementation, before finalizing | Reviews the changes against the plan or user requirements |
| `document-review` | After drafting or revising a non-technical artifact (business doc, product analysis, strategy work, email, spec, etc.) | Performs its own independent analysis from the user's inputs, then compares against your output for fidelity, clarity, logic, completeness, and soundness |
| `analysis-review` | After completing non-trivial analysis that will be returned as a substantial chat response, comment, recommendation, or similar output | Provides an independent second opinion on reasoning, assumptions, completeness, fidelity to the user's request, and actionability |

## Non-negotiables

- Always include every user-typed message from the current session verbatim, in chronological order. Include only the text the user actually typed — do not expand @-mentions, and do not include attached context blocks (open editor tabs, inlined file contents, skill text, git diffs, or other automatically injected context). If the user attached images in any message, save them to the generated per-run images directory and list each resolved absolute image path in the packet.
- **Deduplicate repeated user messages.** If the same user message appears multiple times in your context (from context reloading, conversation resumption, etc.), include it only once at its first chronological occurrence. Deduplicate *before* writing the packet, not after.
- If you cannot recover every prior user message or image, say so explicitly.
- Keep the packet minimal. Do not paste large code excerpts, repository summaries, or diff excerpts unless strictly necessary. Fusion is driven by Codex in a read-only sandbox and inspects the repository directly.
- The OpenRouter API key must be selected from an environment variable, never passed literally. Default to `OPENROUTER_API_KEY`; selectors such as `key:work` resolve to named variables such as `OPENROUTER_API_KEY_WORK`. Never print the key.

## Build the review packet

Compose the packet content in your head first, then write it to disk in one shot using shell commands. **Do not use file-editing tools** (ApplyPatch, WriteFile, EditFile, etc.) for the packet — they are unreliable for temp files and frequently produce residual content, partial overwrites, or stale reads.

First create a unique per-run directory and record the printed paths:

```sh
TMP_BASE="${TMPDIR:-/tmp}"
TMP_BASE="${TMP_BASE%/}"
RUN_DIR="$(mktemp -d "$TMP_BASE/fusion-second-opinion-XXXXXX")"
PACKET_PATH="$RUN_DIR/packet.md"
OUT_PATH="$RUN_DIR/output.txt"
CODEX_LOG="$RUN_DIR/codex.log"
PROXY_LOG="$RUN_DIR/proxy.log"
PROXY_PATH="$RUN_DIR/openrouter-fusion-proxy.py"
IMAGE_DIR="$RUN_DIR/images"
mkdir -p "$IMAGE_DIR"
printf 'Second-opinion run directory: %s\n' "$RUN_DIR"
printf 'Packet path: %s\n' "$PACKET_PATH"
printf 'Output path: %s\n' "$OUT_PATH"
printf 'Codex log path: %s\n' "$CODEX_LOG"
printf 'Proxy log path: %s\n' "$PROXY_LOG"
printf 'Images directory: %s\n' "$IMAGE_DIR"
```

Use the same generated paths for every later step in this invocation. If a later command runs in a fresh shell, substitute the literal paths printed above instead of relying on `$PACKET_PATH`, `$OUT_PATH`, `$CODEX_LOG`, `$PROXY_LOG`, `$PROXY_PATH`, `$IMAGE_DIR`, or `$RUN_DIR` still being defined.

**Required method — shell heredoc or Python one-liner:**

```sh
PACKET_PATH="/var/folders/.../fusion-second-opinion.AbC123/packet.md"
cat > "$PACKET_PATH" << 'PACKET_EOF'
(entire packet content here)
PACKET_EOF
```

Replace the example path with the literal packet path printed during setup.

If the packet is too large for a single heredoc (shell truncation or escaping issues), use a Python one-liner instead:

```sh
PACKET_PATH="/var/folders/.../fusion-second-opinion.AbC123/packet.md"
PACKET_PATH="$PACKET_PATH" python3 -c '
import os
import sys
from pathlib import Path
content = sys.stdin.read()
Path(os.environ["PACKET_PATH"]).write_text(content)
' << 'PACKET_EOF'
(entire packet content here)
PACKET_EOF
```

The packet must contain the sections below — no more, no less.

### Scenario

One of: `independent-rca`, `plan-review`, `post-implementation-review`, `document-review`, `analysis-review`.

### Review target in repository

Tell Fusion what to look at. Examples:
- "Investigate the bug described in the user transcript against the current repository."
- "Evaluate the implementation plan at `docs/plan.md` against the current repository."
- "Review the uncommitted working tree against HEAD."
- "Review commit `<sha>`."
- "Review branch diff `<base>...HEAD`."

Frame the target as work Fusion must independently perform, not as conclusions or verification already established. Explicitly identify only the agent-supplied claims, test results, analysis, or code behavior that materially supports the target or verdict; do not present those load-bearing items as trusted background.

For each load-bearing item, give Fusion a viable verification path before the first run. Prefer direct, already-authorized read-only access to the primary source. When that is unavailable or unnecessary, provide complete primary evidence that permits an independent check, such as the untouched raw export, exact query or request and parameters, analysis command or script, and relevant documentation. A summary of the invoking agent's own verification is not enough. Preflight the actual Fusion invocation—not merely the main agent's environment—to ensure it can read the evidence and run the required safe checks. Never put secrets in the packet or logs.

Do not knowingly launch a review that lacks a required capability merely to obtain `INCOMPLETE`. If a viable path can be prepared without user input or new authority, prepare it first. If an unforeseen access or tooling problem appears in the output, repair it and rerun under the completion-gate procedure. If no viable path can be prepared without the user's help or new authority, stop before the run and report what is needed rather than narrowing the scope.

### Full verbatim user transcript

All user-typed messages from this session, verbatim and in chronological order. Include only the text the user actually typed — do not expand @-mentions, and do not include attached context blocks (open editor tabs, inlined file contents, skill text, git diffs, or other automatically injected context). If the user attached images, note where each image appeared in the conversation and list its resolved absolute path under the generated per-run images directory so Fusion can read it.

### Artifact under review (plan-review, post-implementation-review, document-review, and analysis-review only)

**Omit this entire section for `independent-rca`.** Fusion must not see your analysis — it performs its own from scratch.

- For `plan-review`: if the plan exists as a file on disk, provide only the file path (e.g., "See plan at `docs/plan.md`"). Do NOT copy, paste, or summarize the plan contents into this packet — Fusion will read the file directly through Codex. Only inline the plan text if no plan file exists on disk.
- For `post-implementation-review`: a short implementation summary, intended behavior, and the path to the plan markdown file if one exists (so Fusion can read it). Do not copy plan contents into the packet. Do not include large diff excerpts unless strictly necessary.
- For `document-review`: structure this section in two clearly labeled parts:
  1. **User's request** — what the user asked for (e.g., "analyze competitor pricing," "draft investor email," "recommend a GTM channel"). One sentence.
  2. **Agent's output** — your complete analysis, recommendations, or drafted artifact. If it was written to a file on disk, provide only the file path — do not inline the contents. Inline only if it lives solely in the conversation. Be explicit about which parts are the user's stated inputs and which are your analysis, reasoning, or additions.
- For `analysis-review`: structure this section in two clearly labeled parts:
  1. **User's request** — the analysis or recommendation the user asked for. One sentence.
  2. **Analysis output** — your complete analysis, recommendation, or response draft. If it was written to a file on disk, provide only the file path — do not inline the contents. Inline only if it lives solely in the conversation. Be explicit about key assumptions, evidence, and recommendations.

## Validate the packet before sending

After writing, validate using **shell commands only** (not file-reading tools — they can disagree with the actual file content for temp paths). If this is a new shell command, substitute the literal packet path printed during setup:

```sh
# Structural checks — all must pass
PACKET_PATH="/var/folders/.../fusion-second-opinion.AbC123/packet.md"
echo "=== Structural validation ==="
echo "Scenario count: $(grep -c '^### Scenario' "$PACKET_PATH")"
echo "Artifact count: $(grep -c '^### Artifact under review' "$PACKET_PATH")"
echo "Line count: $(wc -l < "$PACKET_PATH")"
echo "=== First 5 and last 5 lines ==="
head -5 "$PACKET_PATH"
echo "..."
tail -5 "$PACKET_PATH"
```

**Pass criteria:**
- Exactly 1 `### Scenario` heading
- For `independent-rca`: 0 `### Artifact under review` headings
- For `plan-review` / `post-implementation-review` / `document-review` / `analysis-review`: exactly 1 `### Artifact under review` heading
- Line count is reasonable (typically under 200 lines; investigate if over 300)

If structural validation fails, rewrite the packet from scratch at the same generated packet path — do not patch the file.

**Then do a content review.** Read the full file back using `cat /var/folders/.../fusion-second-opinion.AbC123/packet.md` or `cat "$PACKET_PATH"` when `$PACKET_PATH` is defined in the same shell command (not file-reading tools) and check for:

- **Duplicate user messages** — the same message appearing more than once (from context reloading, conversation resumption, etc.). This means deduplication before writing was incomplete.
- **Redundant sections** — the same information stated in multiple places (e.g., the review target restating what's already in the transcript, or the artifact section repeating the review target).
- **Accidentally included context** — attached context blocks, expanded @-mentions, inlined file contents, skill text, or git diffs that leaked into the user transcript.
- **Agent claims framed as established facts** — factual claims, test results, or conclusions from the invoking agent that the review should independently verify but that the packet presents as trusted background.
- **Bloat** — large code excerpts, diff dumps, or repository summaries that Fusion doesn't need (it reads the repo directly through Codex).

If any content issues are found, rewrite the packet from scratch at the same generated packet path — do not patch the file.

## Run Fusion from the repository root

Fusion analysis of a full repo can take several minutes. Complex reviews sometimes take up to 10 minutes and occasionally take 10-20 minutes. Reviews over 30 minutes are suspect; ideally ask the user before killing a long-running review, but around 30 minutes you may decide to kill it using judgment.

This workflow uses Codex as the local read-only repository agent and a temporary localhost proxy to inject OpenRouter's Fusion plugin. The proxy configures the selected Fusion level:

- `medium`: Gemini 3 Flash, Kimi K2.6, and DeepSeek V4 Pro synthesized by Opus 4.8
- `high` (default): Opus 4.8, GPT-5.6-Sol (max effort), and Gemini 3.1 Pro synthesized by Opus 4.8
- `xhigh`: Opus 4.8, GPT-5.6-Sol (max effort), Gemini 3.1 Pro, and DeepSeek V4 Pro synthesized by Opus 4.8

Run this as a shell command. Set `SCENARIO` to match the packet, optionally set `FUSION_LEVEL` by invoking the skill with `medium`, `high`, or `xhigh`, optionally select a key with `key:<name>` or `env:<VAR>`, and substitute the literal packet, output, log, and proxy paths printed during setup.

Inspect the original repository directly by default: keep `REVIEW_ROOT="$REPO_ROOT"` and use the Codex `read-only` sandbox. `read-only` prevents modification of the original repository; it does not hide the repository or substitute a copy for direct inspection. Prefer checks that do not write, such as piping generated input directly to a validator. Only when a material check inherently must write inside its checkout, create a faithful disposable copy of the exact review target under the second-opinion run directory, verify that its diff or artifact hashes match the source target, point the packet and `REVIEW_ROOT` to that copy, and use `workspace-write` only for the disposable copy. Do not use a copy merely for reading or write-free checks, and never make the original repository writable merely to complete a review. If a faithful disposable target cannot be prepared safely, treat the check as unavailable under the completion gate.

```sh
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
REVIEW_ROOT="$REPO_ROOT"
SANDBOX_MODE="read-only"
SCENARIO="independent-rca"  # set to: independent-rca, plan-review, post-implementation-review, document-review, or analysis-review
FUSION_LEVEL="high"
FUSION_LEVEL_SET=""
OPENROUTER_KEY_SELECTOR=""
OPENROUTER_KEY_VAR="OPENROUTER_API_KEY"
CONFIG_ARG="{{args}}"
if [ -n "$CONFIG_ARG" ]; then
  set -- $CONFIG_ARG
  if [ "$#" -gt 2 ]; then
    printf 'Unsupported fusion-second-opinion arguments: %s\nUse no argument for high, a level, a key selector, or "<level> <key-selector>" in any order.\nSupported levels: medium, high, xhigh. Supported key selectors: key:<name>, env:<VAR>.\n' "$CONFIG_ARG" >&2
    exit 2
  fi

  for arg in "$@"; do
    case "$arg" in
      medium|high|xhigh)
        if [ -n "$FUSION_LEVEL_SET" ]; then
          printf 'Duplicate fusion-second-opinion level: %s\nUse only one of: medium, high, xhigh.\n' "$arg" >&2
          exit 2
        fi
        FUSION_LEVEL="$arg"
        FUSION_LEVEL_SET="1"
        ;;
      key:*)
        if [ -n "$OPENROUTER_KEY_SELECTOR" ]; then
          printf 'Duplicate fusion-second-opinion key selector: %s\nUse only one key selector.\n' "$arg" >&2
          exit 2
        fi
        key_name="${arg#key:}"
        if [ -z "$key_name" ]; then
          printf 'Empty fusion-second-opinion key selector: %s\nUse key:<name>, for example key:work.\n' "$arg" >&2
          exit 2
        fi
        case "$key_name" in
          *[!A-Za-z0-9_]*)
            printf 'Unsupported fusion-second-opinion key selector: %s\nkey:<name> may contain only letters, numbers, and underscores.\n' "$arg" >&2
            exit 2
            ;;
        esac
        OPENROUTER_KEY_SELECTOR="$arg"
        key_suffix="$(printf '%s' "$key_name" | tr '[:lower:]' '[:upper:]')"
        OPENROUTER_KEY_VAR="OPENROUTER_API_KEY_$key_suffix"
        ;;
      env:*)
        if [ -n "$OPENROUTER_KEY_SELECTOR" ]; then
          printf 'Duplicate fusion-second-opinion key selector: %s\nUse only one key selector.\n' "$arg" >&2
          exit 2
        fi
        env_name="${arg#env:}"
        if [ -z "$env_name" ]; then
          printf 'Empty fusion-second-opinion env selector: %s\nUse env:<VAR>, for example env:OPENROUTER_API_KEY_WORK.\n' "$arg" >&2
          exit 2
        fi
        OPENROUTER_KEY_SELECTOR="$arg"
        OPENROUTER_KEY_VAR="$env_name"
        ;;
      *)
        printf 'Unsupported fusion-second-opinion argument: %s\nSupported levels: medium, high, xhigh. Supported key selectors: key:<name>, env:<VAR>.\n' "$arg" >&2
        exit 2
        ;;
    esac
  done
fi
PACKET_PATH="/var/folders/.../fusion-second-opinion.AbC123/packet.md"
OUT_PATH="/var/folders/.../fusion-second-opinion.AbC123/output.txt"
CODEX_LOG="/var/folders/.../fusion-second-opinion.AbC123/codex.log"
PROXY_LOG="/var/folders/.../fusion-second-opinion.AbC123/proxy.log"
PROXY_PATH="/var/folders/.../fusion-second-opinion.AbC123/openrouter-fusion-proxy.py"

OPENROUTER_CREDENTIALS="${XDG_CONFIG_HOME:-$HOME/.config}/openrouter/credentials.env"

case "$OPENROUTER_KEY_VAR" in
  [A-Za-z_]*[A-Za-z0-9_]|[A-Za-z_])
    case "$OPENROUTER_KEY_VAR" in
      *[!A-Za-z0-9_]*)
        printf 'Invalid OpenRouter API key environment variable name: %s\n' "$OPENROUTER_KEY_VAR" >&2
        exit 2
        ;;
    esac
    ;;
  *)
    printf 'Invalid OpenRouter API key environment variable name: %s\n' "$OPENROUTER_KEY_VAR" >&2
    exit 2
    ;;
esac

eval "OPENROUTER_SELECTED_KEY=\${$OPENROUTER_KEY_VAR:-}"
if [ -z "$OPENROUTER_SELECTED_KEY" ] && [ -r "$OPENROUTER_CREDENTIALS" ]; then
  set -a
  . "$OPENROUTER_CREDENTIALS"
  set +a
  eval "OPENROUTER_SELECTED_KEY=\${$OPENROUTER_KEY_VAR:-}"
fi

if [ -z "$OPENROUTER_SELECTED_KEY" ]; then
  printf '%s is not set. Export it or store it in %s before running fusion-second-opinion.\n' "$OPENROUTER_KEY_VAR" "$OPENROUTER_CREDENTIALS" >&2
  exit 2
fi
export OPENROUTER_API_KEY="$OPENROUTER_SELECTED_KEY"
unset OPENROUTER_SELECTED_KEY

if ! command -v codex >/dev/null 2>&1; then
  echo "codex CLI is required for fusion-second-opinion because it provides local read-only repository tools." >&2
  exit 2
fi

cat > "$PROXY_PATH" << 'PY'
import http.server
import json
import os
import sys
import urllib.error
import urllib.request
from socketserver import ThreadingMixIn

PORT = int(sys.argv[1])
SYNTHESIZER_MODEL = "anthropic/claude-opus-4.8"
FUSION_LEVEL = os.environ.get("FUSION_LEVEL", "high")
FUSION_LEVELS = {
    "medium": [
        "google/gemini-3-flash-preview",
        "moonshotai/kimi-k2.6",
        "deepseek/deepseek-v4-pro",
    ],
    "high": [
        "anthropic/claude-opus-4.8",
        "openai/gpt-5.6-sol",
        "google/gemini-3.1-pro-preview",
    ],
    "xhigh": [
        "anthropic/claude-opus-4.8",
        "openai/gpt-5.6-sol",
        "google/gemini-3.1-pro-preview",
        "deepseek/deepseek-v4-pro",
    ],
}
if FUSION_LEVEL not in FUSION_LEVELS:
    supported = ", ".join(sorted(FUSION_LEVELS))
    raise SystemExit(f"Unsupported FUSION_LEVEL: {FUSION_LEVEL}. Supported levels: {supported}")

FUSION_PLUGIN = {
    "id": "fusion",
    "model": SYNTHESIZER_MODEL,
    "analysis_models": FUSION_LEVELS[FUSION_LEVEL],
}
HOP_BY_HOP = {"connection", "content-encoding", "content-length", "transfer-encoding"}


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        return

    def audit(self, event, **fields):
        record = {"event": event, **fields}
        print(json.dumps(record, sort_keys=True), file=sys.stderr, flush=True)

    def do_GET(self):
        self.forward(None, "upstream_get_response")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
            if not isinstance(payload, dict):
                raise TypeError("request body must be a JSON object")
            payload["plugins"] = [FUSION_PLUGIN]
            payload["reasoning"] = {"effort": "max"}
            body = json.dumps(payload).encode("utf-8")
            self.audit(
                "fusion_plugin_injected",
                level=FUSION_LEVEL,
                synthesizer=SYNTHESIZER_MODEL,
                analysis_models=FUSION_LEVELS[FUSION_LEVEL],
            )
        except Exception as error:
            self.audit("fusion_plugin_injection_failed", error=f"{type(error).__name__}: {error}")
            return self.respond(500, b"Fusion plugin injection failed", {})
        self.forward(body, "fusion_upstream_response")

    def forward(self, body, success_event):
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            return self.respond(500, b"OPENROUTER_API_KEY is not set", {})

        path = self.path
        if path.startswith("/v1/"):
            path = path[3:]
        url = "https://openrouter.ai/api/v1" + path
        headers = {
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cursor.com",
            "X-Title": "fusion-second-opinion",
        }
        request = urllib.request.Request(url, data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                response_body = response.read()
                self.audit(success_event, status=response.status)
                self.respond(response.status, response_body, response.headers)
        except urllib.error.HTTPError as error:
            error_body = error.read()
            self.audit("upstream_http_error", status=error.code)
            self.respond(error.code, error_body, error.headers)
        except Exception as error:
            self.audit("upstream_error", error=f"{type(error).__name__}: {error}")
            message = f"{type(error).__name__}: {error}".encode("utf-8")
            self.respond(502, message, {})

    def respond(self, status, body, headers):
        self.send_response(status)
        for key, value in headers.items():
            if key.lower() not in HOP_BY_HOP:
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class Server(ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


Server(("127.0.0.1", PORT), Handler).serve_forever()
PY

if [ "$SCENARIO" = "independent-rca" ]; then
  PROMPT="Read the review packet appended below from stdin. You are performing an independent root-cause analysis. The packet contains only the user transcript and a pointer to the repository — do NOT treat it as containing a prior analysis. If the packet references image files, read them. Inspect the repository directly using your read-only tools. Return: your root-cause hypothesis, supporting evidence from the codebase, suggested fix approach, confidence level, and any questions for the user that would help narrow the diagnosis."
elif [ "$SCENARIO" = "plan-review" ]; then
  PROMPT="Read the review packet appended below from stdin. You are reviewing an implementation plan. If the packet references image files, read them. Inspect the repository directly using your read-only tools and use independent judgment. Critique the plan for correctness, completeness, safety, and maintainability. Return: verdict, key issues, recommended changes, missing considerations, and any questions for the user."
elif [ "$SCENARIO" = "document-review" ]; then
  PROMPT="Read the review packet appended below from stdin. You are providing a second opinion on a non-technical artifact (business document, product analysis, strategy work, email, spec, or similar). Work in two phases. PHASE 1 — INDEPENDENT ANALYSIS: Read only the user transcript and inspect the repository for context. Based solely on what the user asked for and the information available, form your own independent analysis, recommendations, or conclusions. Write this up before proceeding to Phase 2. PHASE 2 — COMPARISON: Now read the 'Artifact under review' section containing the other agent's output. Compare your independent conclusions against theirs. Evaluate: (1) fidelity — does the output faithfully reflect what the user actually said, without adding unsupported claims, mischaracterizing user inputs, or injecting assumptions? (2) divergences — where do your conclusions differ, and why? (3) clarity and logic — is the argument coherent, well-structured, and free of gaps? (4) completeness — are there obvious omissions given the user's stated goals? (5) soundness — are conclusions well-supported and recommendations actionable? If the packet references image files, read them. Return: your independent analysis (Phase 1), then the comparison (Phase 2) covering verdict, agreements, divergences with reasoning, fidelity issues, recommended changes, and any questions for the user."
elif [ "$SCENARIO" = "analysis-review" ]; then
  PROMPT="Read the review packet appended below from stdin. You are providing a second opinion on a non-trivial analysis response, recommendation, comment, or similar user-facing output. Work in two phases. PHASE 1 — INDEPENDENT ANALYSIS: Read only the user transcript and inspect the repository for context when relevant. Based solely on what the user asked for and the information available, form your own independent analysis, recommendations, or conclusions. Write this up before proceeding to Phase 2. PHASE 2 — COMPARISON: Now read the 'Artifact under review' section containing the other agent's analysis output. Compare your independent conclusions against theirs. Evaluate: (1) fidelity — does the output answer what the user actually asked, without unsupported claims or mischaracterized inputs? (2) reasoning — are conclusions logically supported by evidence and stated assumptions? (3) divergences — where do your conclusions differ, and why? (4) completeness — are there obvious omissions or unaddressed tradeoffs? (5) actionability — are recommendations concrete enough to use? If the packet references image files, read them. Return: your independent analysis (Phase 1), then the comparison (Phase 2) covering verdict, agreements, divergences with reasoning, fidelity issues, missing considerations, recommended changes, and any questions for the user."
else
  PROMPT="Read the review packet appended below from stdin. You are reviewing a completed implementation. If the packet references image files, read them. Inspect the repository directly using your read-only tools and use independent judgment. Evaluate correctness, safety, maintainability, and fidelity to the plan or user requirements. Return: verdict, key issues, recommended changes, missing tests or checks, and any questions for the user."
fi

COMPLETION_REQUIREMENT='Before returning, verify that you actually read and evaluated the complete intended review target. Independently check the code, analysis, and agent-supplied claims or results that materially support your verdict against primary evidence; do not accept them as established background. Do not expand this requirement to incidental facts outside the requested review scope. User-stated premises remain inputs unless the packet expressly asks you to verify them. Use your read-only shell tools to run safe local validators or tests that are material to the verdict. If a load-bearing item cannot be checked because required evidence, credentials, permissions, or tools are unavailable, the review is incomplete; identify the precise missing capability so the caller can repair it and rerun. A limitation affecting only a non-material point may be disclosed, but do not use that point to support your verdict. Within the first five non-empty lines, write exactly one REVIEW STATUS: COMPLETE line and no REVIEW STATUS: INCOMPLETE line only if every required part was reviewed and every load-bearing item was independently checked; otherwise write exactly one REVIEW STATUS: INCOMPLETE line and no REVIEW STATUS: COMPLETE line. Then identify the concrete repository target, artifacts, checks, and primary evidence you inspected and disclose anything you could not access, evaluate, or verify. Never label a partial review complete.'
PROMPT="$PROMPT $COMPLETION_REQUIREMENT"

PORT="$(python3 - << 'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
)"

FUSION_LEVEL="$FUSION_LEVEL" python3 "$PROXY_PATH" "$PORT" > "$PROXY_LOG" 2>&1 &
PROXY_PID="$!"
trap 'kill "$PROXY_PID" 2>/dev/null || true' EXIT
sleep 1

cd "$REVIEW_ROOT" && codex exec \
  --ephemeral \
  --ignore-user-config \
  --ignore-rules \
  --skip-git-repo-check \
  --sandbox "$SANDBOX_MODE" \
  -C "$REVIEW_ROOT" \
  -m openrouter/fusion \
  -c 'approval_policy="never"' \
  -c 'model_provider="openrouter_fusion_proxy"' \
  -c 'model_providers.openrouter_fusion_proxy={name="OpenRouter Fusion Proxy",base_url="http://127.0.0.1:'"$PORT"'/v1",env_key="OPENROUTER_API_KEY",wire_api="responses"}' \
  -o "$OUT_PATH" \
  "$PROMPT" \
  < "$PACKET_PATH" \
  > "$CODEX_LOG" 2>&1

REVIEW_EXIT="$?"
if [ "$REVIEW_EXIT" -ne 0 ]; then
  printf 'Fusion second-opinion command failed with exit code %s. The review is incomplete; inspect the Codex and proxy logs.\n' "$REVIEW_EXIT" >&2
  exit "$REVIEW_EXIT"
fi
if ! grep -q '"event": "fusion_plugin_injected"' "$PROXY_LOG"; then
  echo "Fusion proxy did not record successful plugin injection. The review is incomplete." >&2
  exit 3
fi
if ! grep -Eq '"event": "fusion_upstream_response".*"status": 2[0-9][0-9]' "$PROXY_LOG"; then
  echo "Fusion proxy did not record a successful upstream response for the plugin-injected POST. The review is incomplete." >&2
  exit 3
fi
if [ ! -s "$OUT_PATH" ]; then
  echo "Fusion second-opinion output is empty. The review is incomplete; inspect the Codex and proxy logs." >&2
  exit 3
fi
REVIEW_WINDOW="$(awk 'NF { print; seen++; if (seen == 5) exit }' "$OUT_PATH" | tr -d '\r' | sed -E 's/^[-[:space:]#>*_`~]+//; s/[-[:space:]*_`~.]+$//')"
REVIEW_COMPLETE_COUNT="$(printf '%s\n' "$REVIEW_WINDOW" | grep -Fxc 'REVIEW STATUS: COMPLETE' || true)"
REVIEW_INCOMPLETE_COUNT="$(printf '%s\n' "$REVIEW_WINDOW" | grep -Fxc 'REVIEW STATUS: INCOMPLETE' || true)"
if [ "$REVIEW_COMPLETE_COUNT" -ne 1 ] || [ "$REVIEW_INCOMPLETE_COUNT" -ne 0 ]; then
  echo "Fusion second-opinion did not provide exactly one COMPLETE marker and no INCOMPLETE marker within its first five non-empty lines. Inspect the output and logs, repair the cause, and rerun." >&2
  exit 3
fi
```

## After the review

1. Read the generated output path, for example `/var/folders/.../fusion-second-opinion.AbC123/output.txt`, and inspect the Codex and proxy logs for execution or panel failures.
2. Apply the review completion gate before doing anything else. If it fails, repair and rerun or stop and report as required above; do not continue with the remaining steps on the strength of an incomplete pass.
3. Once a valid review exists, tell the user the successful second-opinion run directory path so they can inspect the packet, output, and logs if needed.
4. If an earlier attempt failed the completion gate and was repaired, briefly tell the user what failed and what changed before the successful rerun.
5. Fusion's completed feedback is advisory. Use your own judgment throughout.
6. For `independent-rca`: compare Fusion's RCA with your own. Evaluate both and use your best judgment for the fix.
7. For `plan-review` and `post-implementation-review`: apply only material improvements to correctness, safety, maintainability, or clarity.
8. For `document-review` and `analysis-review`: compare Fusion's independent analysis (Phase 1) with your own. Where conclusions diverge, evaluate both on their merits. Correct any fidelity issues Fusion flagged — places where your output diverged from or added to what the user actually said. Apply improvements to clarity, logic, completeness, and actionability only where material.
9. **If Fusion's feedback raises questions needing user input or preference, ask the user rather than making assumptions.**
10. Briefly note any material changes you adopted from the completed review.
