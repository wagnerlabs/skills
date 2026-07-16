---
name: gpt-second-opinion
description: "Sends a time-expensive, blocking review packet to GPT-5.6-Sol at maximum reasoning effort via the Codex CLI, pointed at the full repo in read-only sandbox mode. Use when the user asks or when an agent judges that an independent second opinion would materially improve non-trivial RCA, plans, implementations, documents, or analysis responses; generally at most once per non-trivial task/artifact. Once invoked, the current task must pause until the intended review is verified as substantively complete and considered; repair and rerun a fixable incomplete pass, and do not continue after an unremediable one unless the user explicitly waives the review."
---

# GPT second opinion

## Invocation policy

- Run this skill when the user explicitly asks.
- You may also use it, at your discretion, for non-trivial artifacts where an independent review would materially improve quality.
- This skill is time-expensive and optional by default. It is highly recommended after a non-trivial implementation plan is ready for review, before implementing.
- Once this skill is invoked for a task/artifact, it is **blocking for that task**: do not proceed with the fix, implementation, plan revision, document finalization, user-facing answer, or other reviewed work until the packet has been built and validated, GPT has returned its output, you have verified that GPT actually completed the intended review, you have read the full output, and you have decided which feedback to adopt.
- Do **not** run this skill in parallel while continuing the same workstream. It is acceptable to use a background process only to avoid tool timeouts, but you must wait for completion and consume the review output before advancing the task under review.
- If the intended second-opinion review cannot be completed after safe, in-scope remediation is exhausted, stop the reviewed work and report the failure to the user. Do not proceed unless a valid review later completes or the user explicitly tells you to continue without it.
- Default frequency: at most once per non-trivial task. You may run it once more for a materially different downstream artifact with important differences, such as an implementation that significantly diverged from the reviewed plan. Avoid reruns for minor edits, small follow-ups, or unchanged artifacts.

## Review completion gate

A finished subprocess is not necessarily a finished review. This gate closes the loophole where the command ran but the intended review did not; it does not expand an ordinary review beyond its requested scope or require rechecking incidental background. Before treating this skill as complete, verify all of the following:

- The GPT command exited successfully and produced non-empty, substantive output with exactly one normalized `REVIEW STATUS: COMPLETE` marker and no `REVIEW STATUS: INCOMPLETE` marker within its first five non-empty lines.
- The output identifies the concrete repository target and artifacts GPT inspected and does not disclose any required item as uninspected.
- The output substantively addresses the entire requested scenario and scope. GPT must have used the correct packet, transcript, repository or diff, and every referenced plan, implementation, document, analysis, or image needed for the review. For a two-phase scenario, both phases must be present.
- GPT independently checks the code, analysis, and agent-supplied factual claims, test results, or conclusions that materially support the review target or verdict against primary evidence. The packet must identify those load-bearing items and their verification paths. User-stated premises remain user inputs unless the requested review expressly asks GPT to verify them.
- If evidence, credentials, permissions, or tools needed for a material check are unavailable, the review is incomplete. A limitation affecting only a non-material point may be disclosed without invalidating an otherwise complete review, but GPT must not use that unverified point to support its verdict.
- Neither the output nor the execution evidence reveals an authentication, credential, permission, tool, path, repository, context, or model failure affecting the required scope. Treat a misunderstood packet or scenario, a skipped material target, generic feedback that does not engage with the target, a partial review, or a stated inability to inspect a material or required item as incomplete even if the command exited zero or some useful feedback was returned.

Exactly one `REVIEW STATUS: COMPLETE` marker and no `REVIEW STATUS: INCOMPLETE` marker within the first five non-empty lines is necessary but not sufficient. Read the full output and validate its substance before taking any post-review action. Your own inspection or verification cannot substitute for a missing part of GPT's review.

If the completion gate fails:

1. If the cause can be corrected without user input or new authority, fix it and rerun the second-opinion review. This is required, not optional. Examples include repairing the packet or prompt, correcting a scenario or path, provisioning already-authorized read-only access, adding a complete raw export plus the exact query or analysis command, converting a validator to a write-free form, or preparing a faithful disposable review copy when a material check must write inside its checkout. Do not repeat an unchanged failing command. Validate the replacement output against this gate. Attempts required to obtain the first valid review do not count as additional discretionary reviews under the default-frequency rule.
2. If GPT reviewed only part of the intended scope, treat the whole pass as incomplete. Repair and rerun it; do not fill the gap yourself and continue.
3. Only after safe, in-scope remediation is exhausted, if the review still cannot be completed as intended or the remaining remediation requires unavailable credentials, user input, new authority, or an external state change, **stop the task under review**. This is a pause for the user's decision, not permission to finish the work. Tell the user what failed, what was attempted, and what is needed, and provide the run-directory evidence when available. Do not implement, revise, finalize, or return the reviewed artifact as though the review occurred. Resume only after a valid review completes or the user explicitly directs you to proceed without it.

## Scenarios

Use one of these scenarios:

| Scenario | When | What GPT does |
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
- Keep the packet minimal. Do not paste large code excerpts, repository summaries, or diff excerpts unless strictly necessary. GPT inspects the repository directly and forms its own judgment.

## Build the review packet

Compose the packet content in your head first, then write it to disk in one shot using shell commands. **Do not use file-editing tools** (ApplyPatch, WriteFile, EditFile, etc.) for the packet — they are unreliable for temp files and frequently produce residual content, partial overwrites, or stale reads.

First create a unique per-run directory and record the printed paths:

```sh
TMP_BASE="${TMPDIR:-/tmp}"
TMP_BASE="${TMP_BASE%/}"
RUN_DIR="$(mktemp -d "$TMP_BASE/gpt-second-opinion-XXXXXX")"
PACKET_PATH="$RUN_DIR/packet.md"
OUT_PATH="$RUN_DIR/output.txt"
IMAGE_DIR="$RUN_DIR/images"
mkdir -p "$IMAGE_DIR"
printf 'Second-opinion run directory: %s\n' "$RUN_DIR"
printf 'Packet path: %s\n' "$PACKET_PATH"
printf 'Output path: %s\n' "$OUT_PATH"
printf 'Images directory: %s\n' "$IMAGE_DIR"
```

Use the same generated paths for every later step in this invocation. If a later command runs in a fresh shell, substitute the literal path printed above (for example, `/var/folders/.../gpt-second-opinion.AbC123/packet.md`) instead of relying on `$PACKET_PATH`, `$OUT_PATH`, `$IMAGE_DIR`, or `$RUN_DIR` still being defined.

**Required method — shell heredoc or Python one-liner:**

```sh
PACKET_PATH="/var/folders/.../gpt-second-opinion.AbC123/packet.md"
cat > "$PACKET_PATH" << 'PACKET_EOF'
(entire packet content here)
PACKET_EOF
```

Replace the example path with the literal packet path printed during setup.

If the packet is too large for a single heredoc (shell truncation or escaping issues), use a Python one-liner instead:

```sh
PACKET_PATH="/var/folders/.../gpt-second-opinion.AbC123/packet.md"
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

Tell GPT what to look at. Examples:
- "Investigate the bug described in the user transcript against the current repository."
- "Evaluate the implementation plan at `docs/plan.md` against the current repository."
- "Review the uncommitted working tree against HEAD."
- "Review commit `<sha>`."
- "Review branch diff `<base>...HEAD`."

Frame the target as work GPT must independently perform, not as conclusions or verification already established. Explicitly identify only the agent-supplied claims, test results, analysis, or code behavior that materially supports the target or verdict; do not present those load-bearing items as trusted background.

For each load-bearing item, give GPT a viable verification path before the first run. Prefer direct, already-authorized read-only access to the primary source. When that is unavailable or unnecessary, provide complete primary evidence that permits an independent check, such as the untouched raw export, exact query or request and parameters, analysis command or script, and relevant documentation. A summary of the invoking agent's own verification is not enough. Preflight the actual GPT invocation—not merely the main agent's environment—to ensure it can read the evidence and run the required safe checks. Never put secrets in the packet or logs.

Do not knowingly launch a review that lacks a required capability merely to obtain `INCOMPLETE`. If a viable path can be prepared without user input or new authority, prepare it first. If an unforeseen access or tooling problem appears in the output, repair it and rerun under the completion-gate procedure. If no viable path can be prepared without the user's help or new authority, stop before the run and report what is needed rather than narrowing the scope.

### Full verbatim user transcript

All user-typed messages from this session, verbatim and in chronological order. Include only the text the user actually typed — do not expand @-mentions, and do not include attached context blocks (open editor tabs, inlined file contents, skill text, git diffs, or other automatically injected context). If the user attached images, note where each image appeared in the conversation and list its resolved absolute path under the generated per-run images directory so GPT can read it.

### Artifact under review (plan-review, post-implementation-review, document-review, and analysis-review only)

**Omit this entire section for `independent-rca`.** GPT must not see your analysis — it performs its own from scratch.

- For `plan-review`: if the plan exists as a file on disk, provide only the file path (e.g., "See plan at `docs/plan.md`"). Do NOT copy, paste, or summarize the plan contents into this packet — GPT will read the file directly. Only inline the plan text if no plan file exists on disk.
- For `post-implementation-review`: a short implementation summary, intended behavior, and the path to the plan markdown file if one exists (so GPT can read it). Do not copy plan contents into the packet. Do not include large diff excerpts unless strictly necessary.
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
PACKET_PATH="/var/folders/.../gpt-second-opinion.AbC123/packet.md"
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

**Then do a content review.** Read the full file back using `cat /var/folders/.../gpt-second-opinion.AbC123/packet.md` or `cat "$PACKET_PATH"` when `$PACKET_PATH` is defined in the same shell command (not file-reading tools) and check for:

- **Duplicate user messages** — the same message appearing more than once (from context reloading, conversation resumption, etc.). This means deduplication before writing was incomplete.
- **Redundant sections** — the same information stated in multiple places (e.g., the review target restating what's already in the transcript, or the artifact section repeating the review target).
- **Accidentally included context** — attached context blocks, expanded @-mentions, inlined file contents, skill text, or git diffs that leaked into the user transcript.
- **Agent claims framed as established facts** — factual claims, test results, or conclusions from the invoking agent that the review should independently verify but that the packet presents as trusted background.
- **Bloat** — large code excerpts, diff dumps, or repository summaries that GPT doesn't need (it reads the repo directly).

If any content issues are found, rewrite the packet from scratch at the same generated packet path — do not patch the file.

## Run GPT from the repository root

GPT analysis of a full repo can take several minutes. Complex reviews sometimes take up to 10 minutes and occasionally take 10-20 minutes. Reviews over 30 minutes are suspect; ideally ask the user before killing a long-running review, but around 30 minutes you may decide to kill it using judgment.

Run this as a shell command. Set `SCENARIO` to match the packet, and substitute the literal packet and output paths printed during setup.

Inspect the original repository directly by default: keep `REVIEW_ROOT="$REPO_ROOT"` and use the Codex `read-only` sandbox. `read-only` prevents modification of the original repository; it does not hide the repository or substitute a copy for direct inspection. Prefer checks that do not write, such as piping generated input directly to a validator. Only when a material check inherently must write inside its checkout, create a faithful disposable copy of the exact review target under the second-opinion run directory, verify that its diff or artifact hashes match the source target, point the packet and `REVIEW_ROOT` to that copy, and use `workspace-write` only for the disposable copy. Do not use a copy merely for reading or write-free checks, and never make the original repository writable merely to complete a review. If a faithful disposable target cannot be prepared safely, treat the check as unavailable under the completion gate.

```sh
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
REVIEW_ROOT="$REPO_ROOT"
SANDBOX_MODE="read-only"
SCENARIO="independent-rca"  # set to: independent-rca, plan-review, post-implementation-review, document-review, or analysis-review
PACKET_PATH="/var/folders/.../gpt-second-opinion.AbC123/packet.md"
OUT_PATH="/var/folders/.../gpt-second-opinion.AbC123/output.txt"

if [ "$SCENARIO" = "independent-rca" ]; then
  PROMPT="Read the review packet appended below from stdin. You are performing an independent root-cause analysis. The packet contains only the user transcript and a pointer to the repository — do NOT treat it as containing a prior analysis. If the packet references image files, read them. Inspect the repository directly. Return: your root-cause hypothesis, supporting evidence from the codebase, suggested fix approach, confidence level, and any questions for the user that would help narrow the diagnosis."
elif [ "$SCENARIO" = "plan-review" ]; then
  PROMPT="Read the review packet appended below from stdin. You are reviewing an implementation plan. If the packet references image files, read them. Inspect the repository directly and use independent judgment. Critique the plan for correctness, completeness, safety, and maintainability. Return: verdict, key issues, recommended changes, missing considerations, and any questions for the user."
elif [ "$SCENARIO" = "document-review" ]; then
  PROMPT="Read the review packet appended below from stdin. You are providing a second opinion on a non-technical artifact (business document, product analysis, strategy work, email, spec, or similar). Work in two phases. PHASE 1 — INDEPENDENT ANALYSIS: Read only the user transcript and inspect the repository for context. Based solely on what the user asked for and the information available, form your own independent analysis, recommendations, or conclusions. Write this up before proceeding to Phase 2. PHASE 2 — COMPARISON: Now read the 'Artifact under review' section containing the other agent's output. Compare your independent conclusions against theirs. Evaluate: (1) fidelity — does the output faithfully reflect what the user actually said, without adding unsupported claims, mischaracterizing user inputs, or injecting assumptions? (2) divergences — where do your conclusions differ, and why? (3) clarity and logic — is the argument coherent, well-structured, and free of gaps? (4) completeness — are there obvious omissions given the user's stated goals? (5) soundness — are conclusions well-supported and recommendations actionable? If the packet references image files, read them. Return: your independent analysis (Phase 1), then the comparison (Phase 2) covering verdict, agreements, divergences with reasoning, fidelity issues, recommended changes, and any questions for the user."
elif [ "$SCENARIO" = "analysis-review" ]; then
  PROMPT="Read the review packet appended below from stdin. You are providing a second opinion on a non-trivial analysis response, recommendation, comment, or similar user-facing output. Work in two phases. PHASE 1 — INDEPENDENT ANALYSIS: Read only the user transcript and inspect the repository for context when relevant. Based solely on what the user asked for and the information available, form your own independent analysis, recommendations, or conclusions. Write this up before proceeding to Phase 2. PHASE 2 — COMPARISON: Now read the 'Artifact under review' section containing the other agent's analysis output. Compare your independent conclusions against theirs. Evaluate: (1) fidelity — does the output answer what the user actually asked, without unsupported claims or mischaracterized inputs? (2) reasoning — are conclusions logically supported by evidence and stated assumptions? (3) divergences — where do your conclusions differ, and why? (4) completeness — are there obvious omissions or unaddressed tradeoffs? (5) actionability — are recommendations concrete enough to use? If the packet references image files, read them. Return: your independent analysis (Phase 1), then the comparison (Phase 2) covering verdict, agreements, divergences with reasoning, fidelity issues, missing considerations, recommended changes, and any questions for the user."
else
  PROMPT="Read the review packet appended below from stdin. You are reviewing a completed implementation. If the packet references image files, read them. Inspect the repository directly and use independent judgment. Evaluate correctness, safety, maintainability, and fidelity to the plan or user requirements. Return: verdict, key issues, recommended changes, missing tests or checks, and any questions for the user."
fi

COMPLETION_REQUIREMENT='Before returning, verify that you actually read and evaluated the complete intended review target. Independently check the code, analysis, and agent-supplied claims or results that materially support your verdict against primary evidence; do not accept them as established background. Do not expand this requirement to incidental facts outside the requested review scope. User-stated premises remain inputs unless the packet expressly asks you to verify them. Use your read-only shell tools to run safe local validators or tests that are material to the verdict. If a load-bearing item cannot be checked because required evidence, credentials, permissions, or tools are unavailable, the review is incomplete; identify the precise missing capability so the caller can repair it and rerun. A limitation affecting only a non-material point may be disclosed, but do not use that point to support your verdict. Within the first five non-empty lines, write exactly one REVIEW STATUS: COMPLETE line and no REVIEW STATUS: INCOMPLETE line only if every required part was reviewed and every load-bearing item was independently checked; otherwise write exactly one REVIEW STATUS: INCOMPLETE line and no REVIEW STATUS: COMPLETE line. Then identify the concrete repository target, artifacts, checks, and primary evidence you inspected and disclose anything you could not access, evaluate, or verify. Never label a partial review complete.'
PROMPT="$PROMPT $COMPLETION_REQUIREMENT"

cd "$REVIEW_ROOT" && codex exec \
  -m gpt-5.6-sol \
  -c model_reasoning_effort=max \
  -c approval_policy=never \
  --sandbox "$SANDBOX_MODE" \
  -C "$REVIEW_ROOT" \
  --ephemeral \
  -o "$OUT_PATH" \
  "$PROMPT" \
  < "$PACKET_PATH"

REVIEW_EXIT="$?"
if [ "$REVIEW_EXIT" -ne 0 ]; then
  printf 'GPT second-opinion command failed with exit code %s. The review is incomplete.\n' "$REVIEW_EXIT" >&2
  exit "$REVIEW_EXIT"
fi
if [ ! -s "$OUT_PATH" ]; then
  echo "GPT second-opinion output is empty. The review is incomplete." >&2
  exit 3
fi
REVIEW_WINDOW="$(awk 'NF { print; seen++; if (seen == 5) exit }' "$OUT_PATH" | tr -d '\r' | sed -E 's/^[-[:space:]#>*_`~]+//; s/[-[:space:]*_`~.]+$//')"
REVIEW_COMPLETE_COUNT="$(printf '%s\n' "$REVIEW_WINDOW" | grep -Fxc 'REVIEW STATUS: COMPLETE' || true)"
REVIEW_INCOMPLETE_COUNT="$(printf '%s\n' "$REVIEW_WINDOW" | grep -Fxc 'REVIEW STATUS: INCOMPLETE' || true)"
if [ "$REVIEW_COMPLETE_COUNT" -ne 1 ] || [ "$REVIEW_INCOMPLETE_COUNT" -ne 0 ]; then
  echo "GPT second-opinion did not provide exactly one COMPLETE marker and no INCOMPLETE marker within its first five non-empty lines. Inspect the output, repair the cause, and rerun." >&2
  exit 3
fi
```

## After the review

1. Read the generated output path, for example `/var/folders/.../gpt-second-opinion.AbC123/output.txt`.
2. Apply the review completion gate before doing anything else. If it fails, repair and rerun or stop and report as required above; do not continue with the remaining steps on the strength of an incomplete pass.
3. Once a valid review exists, tell the user the successful second-opinion run directory path so they can inspect the packet and output if needed.
4. If an earlier attempt failed the completion gate and was repaired, briefly tell the user what failed and what changed before the successful rerun.
5. GPT's completed feedback is advisory. Use your own judgment throughout.
6. For `independent-rca`: compare GPT's RCA with your own. Evaluate both and use your best judgment for the fix.
7. For `plan-review` and `post-implementation-review`: apply only material improvements to correctness, safety, maintainability, or clarity.
8. For `document-review` and `analysis-review`: compare GPT's independent analysis (Phase 1) with your own. Where conclusions diverge, evaluate both on their merits. Correct any fidelity issues GPT flagged — places where your output diverged from or added to what the user actually said. Apply improvements to clarity, logic, completeness, and actionability only where material.
9. **If GPT's feedback raises questions needing user input or preference, ask the user rather than making assumptions.**
10. Briefly note any material changes you adopted from the completed review.
