---
name: claude-second-opinion
description: "User-invoked only — do NOT run automatically. Sends a review packet to Claude Opus 4.6 via the CLI, pointed at the full repo in read-only mode. The user will explicitly ask for this when they want it."
---

# Claude second opinion

> **This skill is user-invoked only.** Do not run it automatically after implementation, RCA, or planning. Wait for the user to explicitly request it.

Choose the scenario based on what you just completed:

- You just finished investigating a bug (RCA) and have not started fixing it → `independent-rca`. Claude performs its own independent RCA from scratch — does NOT see yours.
- You just created or updated a plan document (for a bug fix, feature, or anything else) → `plan-review`. Claude reviews and critiques the plan.
- You just finished implementing code changes → `post-implementation-review`. Claude reviews the changes against the plan or user requirements.

## Non-negotiables

- Always include every user-typed message from the current session verbatim, in chronological order. Include only the text the user actually typed — do not expand @-mentions, and do not include attached context blocks (open editor tabs, inlined file contents, skill text, git diffs, or other automatically injected context). If the user attached images in any message, save them to `/tmp/claude-second-opinion-images/` and list their paths in the packet.
- **Deduplicate repeated user messages.** If the same user message appears multiple times in your context (from context reloading, conversation resumption, etc.), include it only once at its first chronological occurrence. Deduplicate *before* writing the packet, not after.
- If you cannot recover every prior user message or image, say so explicitly.
- Keep the packet minimal. Do not paste large code excerpts, repository summaries, or diff excerpts unless strictly necessary. Claude inspects the repository directly and forms its own judgment.

## Build the review packet

Compose the packet content in your head first, then write it to disk in one shot using shell commands. **Do not use file-editing tools** (ApplyPatch, WriteFile, EditFile, etc.) for `/tmp/claude-second-opinion.md` — they are unreliable for temp files and frequently produce residual content, partial overwrites, or stale reads.

**Required method — shell heredoc or Python one-liner:**

```sh
rm -f /tmp/claude-second-opinion.md
cat > /tmp/claude-second-opinion.md << 'PACKET_EOF'
(entire packet content here)
PACKET_EOF
```

If the packet is too large for a single heredoc (shell truncation or escaping issues), use a Python one-liner instead:

```sh
rm -f /tmp/claude-second-opinion.md
python3 -c "
import sys
content = sys.stdin.read()
with open('/tmp/claude-second-opinion.md', 'w') as f:
    f.write(content)
" << 'PACKET_EOF'
(entire packet content here)
PACKET_EOF
```

The packet must contain the sections below — no more, no less.

### Scenario

One of: `independent-rca`, `plan-review`, `post-implementation-review`.

### Review target in repository

Tell Claude what to look at. Examples:
- "Investigate the bug described in the user transcript against the current repository."
- "Evaluate the implementation plan at `docs/plan.md` against the current repository."
- "Review the uncommitted working tree against HEAD."
- "Review commit `<sha>`."
- "Review branch diff `<base>...HEAD`."

### Full verbatim user transcript

All user-typed messages from this session, verbatim and in chronological order. Include only the text the user actually typed — do not expand @-mentions, and do not include attached context blocks (open editor tabs, inlined file contents, skill text, git diffs, or other automatically injected context). If the user attached images, note where each image appeared in the conversation and list its path under `/tmp/claude-second-opinion-images/` so Claude can read it.

### Artifact under review (plan-review and post-implementation-review only)

**Omit this entire section for `independent-rca`.** Claude must not see your analysis — it performs its own from scratch.

- For `plan-review`: if the plan exists as a file on disk, provide only the file path (e.g., "See plan at `docs/plan.md`"). Do NOT copy, paste, or summarize the plan contents into this packet — Claude will read the file directly. Only inline the plan text if no plan file exists on disk.
- For `post-implementation-review`: a short implementation summary, intended behavior, and the path to the plan markdown file if one exists (so Claude can read it). Do not copy plan contents into the packet. Do not include large diff excerpts unless strictly necessary.

## Validate the packet before sending

After writing, validate using **shell commands only** (not file-reading tools — they can disagree with the actual file content for `/tmp` paths):

```sh
# Structural checks — all must pass
echo "=== Structural validation ==="
echo "Scenario count: $(grep -c '^### Scenario' /tmp/claude-second-opinion.md)"
echo "Artifact count: $(grep -c '^### Artifact under review' /tmp/claude-second-opinion.md)"
echo "Line count: $(wc -l < /tmp/claude-second-opinion.md)"
echo "=== First 5 and last 5 lines ==="
head -5 /tmp/claude-second-opinion.md
echo "..."
tail -5 /tmp/claude-second-opinion.md
```

**Pass criteria:**
- Exactly 1 `### Scenario` heading
- For `independent-rca`: 0 `### Artifact under review` headings
- For `plan-review` / `post-implementation-review`: exactly 1 `### Artifact under review` heading
- Line count is reasonable (typically under 200 lines; investigate if over 300)

If structural validation fails, `rm -f /tmp/claude-second-opinion.md` and rewrite from scratch — do not patch the file.

**Then do a content review.** Read the full file back using `cat /tmp/claude-second-opinion.md` (not file-reading tools) and check for:

- **Duplicate user messages** — the same message appearing more than once (from context reloading, conversation resumption, etc.). This means deduplication before writing was incomplete.
- **Redundant sections** — the same information stated in multiple places (e.g., the review target restating what's already in the transcript, or the artifact section repeating the review target).
- **Accidentally included context** — attached context blocks, expanded @-mentions, inlined file contents, skill text, or git diffs that leaked into the user transcript.
- **Bloat** — large code excerpts, diff dumps, or repository summaries that Claude doesn't need (it reads the repo directly).

If any content issues are found, `rm -f /tmp/claude-second-opinion.md` and rewrite from scratch — do not patch the file.

## Run Claude from the repository root

Run this as a shell command. Set `SCENARIO` to match the packet.

```sh
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCENARIO="independent-rca"  # set to: independent-rca, plan-review, or post-implementation-review

if [ "$SCENARIO" = "independent-rca" ]; then
  PROMPT="Read the review packet from stdin. You are performing an independent root-cause analysis. The packet contains only the user transcript and a pointer to the repository — do NOT treat it as containing a prior analysis. If the packet references image files, read them with the Read tool. Inspect the repository directly using your allowed tools. Return: your root-cause hypothesis, supporting evidence from the codebase, suggested fix approach, confidence level, and any questions for the user that would help narrow the diagnosis."
elif [ "$SCENARIO" = "plan-review" ]; then
  PROMPT="Read the review packet from stdin. You are reviewing an implementation plan. If the packet references image files, read them with the Read tool. Inspect the repository directly using your allowed tools and use independent judgment. Critique the plan for correctness, completeness, safety, and maintainability. Return: verdict, key issues, recommended changes, missing considerations, and any questions for the user."
else
  PROMPT="Read the review packet from stdin. You are reviewing a completed implementation. If the packet references image files, read them with the Read tool. Inspect the repository directly using your allowed tools and use independent judgment. Evaluate correctness, safety, maintainability, and fidelity to the plan or user requirements. Return: verdict, key issues, recommended changes, missing tests or checks, and any questions for the user."
fi

cd "$REPO_ROOT" && claude -p \
  --model claude-opus-4-6 \
  --effort max \
  --permission-mode default \
  --tools "Bash,Read,Grep,Glob" \
  --allowedTools "Read,Grep,Glob,Bash(pwd),Bash(ls:*),Bash(git:*)" \
  --max-turns 100 \
  --output-format text \
  "$PROMPT" \
  < /tmp/claude-second-opinion.md \
  > /tmp/claude-second-opinion.out.txt
```

## After the review

1. Read `/tmp/claude-second-opinion.out.txt`.
2. Claude's feedback is advisory. Use your own judgment throughout.
3. For `independent-rca`: compare Claude's RCA with your own. Evaluate both and use your best judgment for the fix.
4. For `plan-review` and `post-implementation-review`: apply only material improvements to correctness, safety, maintainability, or clarity.
5. **If Claude's feedback raises questions needing user input or preference, ask the user rather than making assumptions.**
6. Briefly note any material changes you adopted from the review.
7. If the Claude review could not be run, say that explicitly before proceeding.
