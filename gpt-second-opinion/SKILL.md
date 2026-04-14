---
name: gpt-second-opinion
description: "User-invoked only — do NOT run automatically. Sends a review packet to GPT-5.4 via the Codex CLI, pointed at the full repo in read-only sandbox mode. The user will explicitly ask for this when they want it."
---

# GPT second opinion

> **This skill is user-invoked only.** Do not run it automatically after implementation, RCA, or planning. Wait for the user to explicitly request it.

Invoke at one of four checkpoints:

| Scenario | When | What GPT does |
|---|---|---|
| `independent-rca` | After your own RCA, before fixing a bug | Performs its own independent RCA from scratch — does NOT see yours |
| `plan-review` | After drafting a feature plan, before implementing | Reviews and critiques the plan |
| `post-implementation-review` | After implementation, before finalizing | Reviews the changes against the plan or user requirements |
| `document-review` | After drafting or revising a non-technical artifact (business doc, product analysis, strategy work, email, spec, etc.) | Performs its own independent analysis from the user's inputs, then compares against Claude's output for fidelity, clarity, logic, completeness, and soundness |

## Non-negotiables

- Always include every user-typed message from the current session verbatim, in chronological order. Include only the text the user actually typed — do not expand @-mentions, and do not include attached context blocks (open editor tabs, inlined file contents, skill text, git diffs, or other automatically injected context). If the user attached images in any message, save them to `/tmp/gpt-second-opinion-images/` and list their paths in the packet.
- **Deduplicate repeated user messages.** If the same user message appears multiple times in your context (from context reloading, conversation resumption, etc.), include it only once at its first chronological occurrence. Deduplicate *before* writing the packet, not after.
- If you cannot recover every prior user message or image, say so explicitly.
- Keep the packet minimal. Do not paste large code excerpts, repository summaries, or diff excerpts unless strictly necessary. GPT inspects the repository directly and forms its own judgment.

## Build the review packet

Compose the packet content in your head first, then write it to disk in one shot using shell commands. **Do not use file-editing tools** (ApplyPatch, WriteFile, EditFile, etc.) for `/tmp/gpt-second-opinion.md` — they are unreliable for temp files and frequently produce residual content, partial overwrites, or stale reads.

**Required method — shell heredoc or Python one-liner:**

```sh
rm -f /tmp/gpt-second-opinion.md
cat > /tmp/gpt-second-opinion.md << 'PACKET_EOF'
(entire packet content here)
PACKET_EOF
```

If the packet is too large for a single heredoc (shell truncation or escaping issues), use a Python one-liner instead:

```sh
rm -f /tmp/gpt-second-opinion.md
python3 -c "
import sys
content = sys.stdin.read()
with open('/tmp/gpt-second-opinion.md', 'w') as f:
    f.write(content)
" << 'PACKET_EOF'
(entire packet content here)
PACKET_EOF
```

The packet must contain the sections below — no more, no less.

### Scenario

One of: `independent-rca`, `plan-review`, `post-implementation-review`, `document-review`.

### Review target in repository

Tell GPT what to look at. Examples:
- "Investigate the bug described in the user transcript against the current repository."
- "Evaluate the implementation plan at `docs/plan.md` against the current repository."
- "Review the uncommitted working tree against HEAD."
- "Review commit `<sha>`."
- "Review branch diff `<base>...HEAD`."

### Full verbatim user transcript

All user-typed messages from this session, verbatim and in chronological order. Include only the text the user actually typed — do not expand @-mentions, and do not include attached context blocks (open editor tabs, inlined file contents, skill text, git diffs, or other automatically injected context). If the user attached images, note where each image appeared in the conversation and list its path under `/tmp/gpt-second-opinion-images/` so GPT can read it.

### Artifact under review (plan-review, post-implementation-review, and document-review only)

**Omit this entire section for `independent-rca`.** GPT must not see your analysis — it performs its own from scratch.

- For `plan-review`: if the plan exists as a file on disk, provide only the file path (e.g., "See plan at `docs/plan.md`"). Do NOT copy, paste, or summarize the plan contents into this packet — GPT will read the file directly. Only inline the plan text if no plan file exists on disk.
- For `post-implementation-review`: a short implementation summary, intended behavior, and the path to the plan markdown file if one exists (so GPT can read it). Do not copy plan contents into the packet. Do not include large diff excerpts unless strictly necessary.
- For `document-review`: structure this section in two clearly labeled parts:
  1. **User's request** — what the user asked for (e.g., "analyze competitor pricing," "draft investor email," "recommend a GTM channel"). One sentence.
  2. **Claude's output** — your complete analysis, recommendations, or drafted artifact. If it was written to a file on disk, provide only the file path — do not inline the contents. Inline only if it lives solely in the conversation. Be explicit about which parts are the user's stated inputs and which are your analysis, reasoning, or additions.

## Validate the packet before sending

After writing, validate using **shell commands only** (not file-reading tools — they can disagree with the actual file content for `/tmp` paths):

```sh
# Structural checks — all must pass
echo "=== Structural validation ==="
echo "Scenario count: $(grep -c '^### Scenario' /tmp/gpt-second-opinion.md)"
echo "Artifact count: $(grep -c '^### Artifact under review' /tmp/gpt-second-opinion.md)"
echo "Line count: $(wc -l < /tmp/gpt-second-opinion.md)"
echo "=== First 5 and last 5 lines ==="
head -5 /tmp/gpt-second-opinion.md
echo "..."
tail -5 /tmp/gpt-second-opinion.md
```

**Pass criteria:**
- Exactly 1 `### Scenario` heading
- For `independent-rca`: 0 `### Artifact under review` headings
- For `plan-review` / `post-implementation-review` / `document-review`: exactly 1 `### Artifact under review` heading
- Line count is reasonable (typically under 200 lines; investigate if over 300)

If structural validation fails, `rm -f /tmp/gpt-second-opinion.md` and rewrite from scratch — do not patch the file.

**Then do a content review.** Read the full file back using `cat /tmp/gpt-second-opinion.md` (not file-reading tools) and check for:

- **Duplicate user messages** — the same message appearing more than once (from context reloading, conversation resumption, etc.). This means deduplication before writing was incomplete.
- **Redundant sections** — the same information stated in multiple places (e.g., the review target restating what's already in the transcript, or the artifact section repeating the review target).
- **Accidentally included context** — attached context blocks, expanded @-mentions, inlined file contents, skill text, or git diffs that leaked into the user transcript.
- **Bloat** — large code excerpts, diff dumps, or repository summaries that GPT doesn't need (it reads the repo directly).

If any content issues are found, `rm -f /tmp/gpt-second-opinion.md` and rewrite from scratch — do not patch the file.

## Run GPT from the repository root

**Important: use a 10-minute timeout when executing this command, as GPT analysis of a full repo can take several minutes.**

Run this as a shell command. Set `SCENARIO` to match the packet.

```sh
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCENARIO="independent-rca"  # set to: independent-rca, plan-review, post-implementation-review, or document-review

if [ "$SCENARIO" = "independent-rca" ]; then
  PROMPT="Read the review packet appended below from stdin. You are performing an independent root-cause analysis. The packet contains only the user transcript and a pointer to the repository — do NOT treat it as containing a prior analysis. If the packet references image files, read them. Inspect the repository directly. Return: your root-cause hypothesis, supporting evidence from the codebase, suggested fix approach, confidence level, and any questions for the user that would help narrow the diagnosis."
elif [ "$SCENARIO" = "plan-review" ]; then
  PROMPT="Read the review packet appended below from stdin. You are reviewing an implementation plan. If the packet references image files, read them. Inspect the repository directly and use independent judgment. Critique the plan for correctness, completeness, safety, and maintainability. Return: verdict, key issues, recommended changes, missing considerations, and any questions for the user."
elif [ "$SCENARIO" = "document-review" ]; then
  PROMPT="Read the review packet appended below from stdin. You are providing a second opinion on a non-technical artifact (business document, product analysis, strategy work, email, spec, or similar). Work in two phases. PHASE 1 — INDEPENDENT ANALYSIS: Read only the user transcript and inspect the repository for context. Based solely on what the user asked for and the information available, form your own independent analysis, recommendations, or conclusions. Write this up before proceeding to Phase 2. PHASE 2 — COMPARISON: Now read the 'Artifact under review' section containing Claude's output. Compare your independent conclusions against Claude's. Evaluate: (1) fidelity — does Claude's output faithfully reflect what the user actually said, without adding unsupported claims, mischaracterizing user inputs, or injecting assumptions? (2) divergences — where do your conclusions differ from Claude's, and why? (3) clarity and logic — is the argument coherent, well-structured, and free of gaps? (4) completeness — are there obvious omissions given the user's stated goals? (5) soundness — are conclusions well-supported and recommendations actionable? If the packet references image files, read them. Return: your independent analysis (Phase 1), then the comparison (Phase 2) covering verdict, agreements, divergences with reasoning, fidelity issues, recommended changes, and any questions for the user."
else
  PROMPT="Read the review packet appended below from stdin. You are reviewing a completed implementation. If the packet references image files, read them. Inspect the repository directly and use independent judgment. Evaluate correctness, safety, maintainability, and fidelity to the plan or user requirements. Return: verdict, key issues, recommended changes, missing tests or checks, and any questions for the user."
fi

cd "$REPO_ROOT" && codex exec \
  -m gpt-5.4 \
  -c model_reasoning_effort=xhigh \
  -c approval_policy=never \
  --sandbox read-only \
  -C "$REPO_ROOT" \
  --ephemeral \
  -o /tmp/gpt-second-opinion.out.txt \
  "$PROMPT" \
  < /tmp/gpt-second-opinion.md
```

## After the review

1. Read `/tmp/gpt-second-opinion.out.txt`.
2. GPT's feedback is advisory. Use your own judgment throughout.
3. For `independent-rca`: compare GPT's RCA with your own. Evaluate both and use your best judgment for the fix.
4. For `plan-review` and `post-implementation-review`: apply only material improvements to correctness, safety, maintainability, or clarity.
5. For `document-review`: compare GPT's independent analysis (Phase 1) with your own. Where conclusions diverge, evaluate both on their merits. Correct any fidelity issues GPT flagged — places where your output diverged from or added to what the user actually said. Apply improvements to clarity, logic, and completeness only where material.
6. **If GPT's feedback raises questions needing user input or preference, ask the user rather than making assumptions.**
7. Briefly note any material changes you adopted from the review.
8. If the GPT review could not be run, say that explicitly before proceeding.
