---
name: fusion-second-opinion
description: "Sends a time-expensive, blocking review packet to OpenRouter Fusion via Codex CLI in a read-only sandbox, using Gemini 3 Flash, Kimi K2.6, and DeepSeek V4 Pro as analysis models synthesized by Claude Opus 4.8 through the OpenRouter API. Use when the user asks or when an agent judges that an independent multi-model second opinion would materially improve non-trivial RCA, plans, implementations, documents, or analysis responses; generally at most once per non-trivial task/artifact. Once invoked, the current task must pause until the Fusion review is complete and considered."
---

# Fusion second opinion

## Invocation policy

- Run this skill when the user explicitly asks.
- You may also use it, at your discretion, for non-trivial artifacts where an independent multi-model review would materially improve quality.
- This skill is time-expensive and optional by default. It is highly recommended after a non-trivial implementation plan is ready for review, before implementing.
- Once this skill is invoked for a task/artifact, it is **blocking for that task**: do not proceed with the fix, implementation, plan revision, document finalization, user-facing answer, or other reviewed work until the packet has been built and validated, Fusion has returned its output, you have read the output, and you have decided which feedback to adopt.
- Do **not** run this skill in parallel while continuing the same workstream. It is acceptable to use a background process only to avoid tool timeouts, but you must wait for completion and consume the review output before advancing the task under review.
- If the second-opinion run cannot be completed, explicitly tell the user it could not be run before proceeding; do not silently continue as if the blocking review happened.
- Default frequency: at most once per non-trivial task. You may run it once more for a materially different downstream artifact with important differences, such as an implementation that significantly diverged from the reviewed plan. Avoid reruns for minor edits, small follow-ups, or unchanged artifacts.

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
- The OpenRouter API key must come from `OPENROUTER_API_KEY`, either already exported or stored in `${XDG_CONFIG_HOME:-$HOME/.config}/openrouter/credentials.env`. Never print the key.

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
- **Bloat** — large code excerpts, diff dumps, or repository summaries that Fusion doesn't need (it reads the repo directly through Codex).

If any content issues are found, rewrite the packet from scratch at the same generated packet path — do not patch the file.

## Run Fusion from the repository root

Fusion analysis of a full repo can take several minutes. Complex reviews sometimes take up to 10 minutes and occasionally take 10-20 minutes. Reviews over 30 minutes are suspect; ideally ask the user before killing a long-running review, but around 30 minutes you may decide to kill it using judgment.

This workflow uses Codex as the local read-only repository agent and a temporary localhost proxy to inject OpenRouter's Fusion plugin. The proxy configures:

- Judge/synthesizer: `anthropic/claude-opus-4.8`
- Analysis panel: `google/gemini-3-flash-preview`, `moonshotai/kimi-k2.6`, `deepseek/deepseek-v4-pro`

Run this as a shell command. Set `SCENARIO` to match the packet, and substitute the literal packet, output, log, and proxy paths printed during setup.

```sh
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCENARIO="independent-rca"  # set to: independent-rca, plan-review, post-implementation-review, document-review, or analysis-review
PACKET_PATH="/var/folders/.../fusion-second-opinion.AbC123/packet.md"
OUT_PATH="/var/folders/.../fusion-second-opinion.AbC123/output.txt"
CODEX_LOG="/var/folders/.../fusion-second-opinion.AbC123/codex.log"
PROXY_LOG="/var/folders/.../fusion-second-opinion.AbC123/proxy.log"
PROXY_PATH="/var/folders/.../fusion-second-opinion.AbC123/openrouter-fusion-proxy.py"

OPENROUTER_CREDENTIALS="${XDG_CONFIG_HOME:-$HOME/.config}/openrouter/credentials.env"
if [ -z "${OPENROUTER_API_KEY:-}" ] && [ -r "$OPENROUTER_CREDENTIALS" ]; then
  set -a
  . "$OPENROUTER_CREDENTIALS"
  set +a
fi

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "OPENROUTER_API_KEY is not set. Export it or store it in $OPENROUTER_CREDENTIALS before running fusion-second-opinion." >&2
  exit 2
fi

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
FUSION_PLUGIN = {
    "id": "fusion",
    "model": "anthropic/claude-opus-4.8",
    "analysis_models": [
        "google/gemini-3-flash-preview",
        "moonshotai/kimi-k2.6",
        "deepseek/deepseek-v4-pro",
    ],
}
HOP_BY_HOP = {"connection", "content-encoding", "content-length", "transfer-encoding"}


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        self.forward(None)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
            payload["plugins"] = [FUSION_PLUGIN]
            body = json.dumps(payload).encode("utf-8")
        except Exception:
            pass
        self.forward(body)

    def forward(self, body):
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
                self.respond(response.status, response.read(), response.headers)
        except urllib.error.HTTPError as error:
            self.respond(error.code, error.read(), error.headers)
        except Exception as error:
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

PORT="$(python3 - << 'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
)"

python3 "$PROXY_PATH" "$PORT" > "$PROXY_LOG" 2>&1 &
PROXY_PID="$!"
trap 'kill "$PROXY_PID" 2>/dev/null || true' EXIT
sleep 1

cd "$REPO_ROOT" && codex exec \
  --ephemeral \
  --ignore-user-config \
  --ignore-rules \
  --skip-git-repo-check \
  --sandbox read-only \
  -C "$REPO_ROOT" \
  -m openrouter/fusion \
  -c 'approval_policy="never"' \
  -c 'model_provider="openrouter_fusion_proxy"' \
  -c 'model_providers.openrouter_fusion_proxy={name="OpenRouter Fusion Proxy",base_url="http://127.0.0.1:'"$PORT"'/v1",env_key="OPENROUTER_API_KEY",wire_api="responses"}' \
  -o "$OUT_PATH" \
  "$PROMPT" \
  < "$PACKET_PATH" \
  > "$CODEX_LOG" 2>&1
```

## After the review

1. Tell the user the second-opinion run directory path so they can inspect the packet, output, and logs if needed.
2. Read the generated output path, for example `/var/folders/.../fusion-second-opinion.AbC123/output.txt`.
3. Fusion's feedback is advisory. Use your own judgment throughout.
4. For `independent-rca`: compare Fusion's RCA with your own. Evaluate both and use your best judgment for the fix.
5. For `plan-review` and `post-implementation-review`: apply only material improvements to correctness, safety, maintainability, or clarity.
6. For `document-review` and `analysis-review`: compare Fusion's independent analysis (Phase 1) with your own. Where conclusions diverge, evaluate both on their merits. Correct any fidelity issues Fusion flagged — places where your output diverged from or added to what the user actually said. Apply improvements to clarity, logic, completeness, and actionability only where material.
7. **If Fusion's feedback raises questions needing user input or preference, ask the user rather than making assumptions.**
8. Briefly note any material changes you adopted from the review.
9. If the Fusion review could not be run, say that explicitly before proceeding.
