# Second-opinion skill investigation ledger

## Scope

- Identify the change that made second-opinion use slower or iterative.
- Preserve the hard gate when an invoked review cannot actually run or cannot inspect required material.
- Ensure a completed review remains advisory: the invoking agent decides which feedback to adopt, and reviewer disagreement alone never requires a rerun.
- Update `claude-second-opinion`, `gpt-second-opinion`, and the tracked `fusion-second-opinion` consistently if the evidence supports a change.
- Preserve unrelated working-tree changes, especially the untracked `fusion-second-opinion/` files.
- Route single-model second opinions toward a different model provider from the invoking agent to improve diversity of perspective.
- Reserve Fusion for high-stakes, explicitly user-requested reviews because its multi-model panel consumes more quota or credits.

## User decisions and constraints

- A required review must not be casually skipped after authentication, access, packet, or execution failure.
- A reviewer must not become the authority over the main agent's plan or implementation.
- Feedback does not need to be accepted wholesale, and a valid review should not be rerun merely to seek agreement or approval.
- Operational success requires the reviewer to access every critical/load-bearing related material. A zero exit code, `COMPLETE` marker, or useful partial review does not override a disclosed inability to inspect such material.
- GPT/OpenAI-based agents should generally prefer `claude-second-opinion`; non-GPT/OpenAI agents are the primary audience for `gpt-second-opinion`.
- Claude/Anthropic-based agents should generally prefer `gpt-second-opinion`; non-Claude/Anthropic agents are the primary audience for `claude-second-opinion`.
- Agents must never invoke `fusion-second-opinion` autonomously. Run it only when the user explicitly requests Fusion.

## Completed

- Read the repository-level instructions supplied by the user.
- Read the complete `skill-creator` instructions.
- Confirmed the working tree contains unrelated untracked `fusion-second-opinion/` content that must remain untouched.
- Located likely history pivots: `b7bf7ff` (`docs: make second-opinion skills blocking`) and `1448374` (`fix: enforce complete second-opinion reviews`).
- Compared the July 15 change against its parent and confirmed that it added mandatory review-status markers, broad independent-verification requirements, and required reruns for every pass classified as incomplete.
- Confirmed the pre-change post-review rule already made feedback advisory and left adoption to the invoking agent; the July 15 change retained that rule but placed stronger, ambiguous completion language ahead of it.
- Updated the Claude, GPT, and tracked Fusion skills so the completion gate explicitly measures execution/access/coverage rather than artifact quality or reviewer agreement.
- Updated the embedded reviewer prompts so a critical or rejecting verdict still returns `REVIEW STATUS: COMPLETE` when the requested review was actually performed.
- Limited reruns to concrete execution, access, packet, panel/synthesis, or coverage failures; explicitly prohibited revise/resubmit approval loops.
- Narrowed ordinary reviews so they independently inspect necessary primary material without automatically reproducing every test or incidental claim.
- Validated all three skill folders with `quick_validate.py`.
- Syntax-checked all three embedded launch blocks with `bash -n` without invoking a review model.
- Ran focused semantic assertions proving each skill retains the hard stop for failed reviews and contains the advisory/no-approval-loop rules.
- Simulated the output-marker gate: a `COMPLETE` review with a rejecting verdict passes, while an `INCOMPLETE` review caused by an unreadable plan fails.
- Ran `git diff --check`; it passed.
- Clarified that operational success requires access to every critical/load-bearing related material, not merely successful process execution or a `COMPLETE` marker.
- Clarified that “could not access X” is an operational failure requiring remediation and rerun when X is critical/load-bearing, even if the remainder of the feedback is useful.
- Preserved the distinction between inaccessible referenced material and an omission within the reviewed artifact that should be reported as feedback.
- Revalidated all three skills after the clarification.
- Added cross-provider routing so Claude/Anthropic agents prefer GPT reviews and GPT/OpenAI agents prefer Claude reviews when the user has not specified a reviewer.
- Kept explicit user reviewer choices and concrete task constraints as overrides to the default diversity preference.
- Made Fusion strictly user-invoked; a generic request for a second opinion no longer authorizes Fusion.
- Added high-stakes positioning and quota/credit cost guidance for Fusion and its selectable panels.
- Standardized Fusion cost wording on “credits.”
- Compressed all three frontmatter descriptions below the validator's 1,024-character limit without removing the routing or authorization rules.
- Revalidated all three updated skills, embedded launch blocks, semantic routing invariants, and the final diff.
- Confirmed no `paid-credit` or equivalent wording remains in the Fusion skill or task ledger.

## Current work

- Commit and push the validated provider-routing and Fusion policy update.

## Remaining work

- Stage only the three tracked skill files and this ledger, leaving pre-existing untracked Fusion materials untouched.
- Commit, push, and verify remote `main`.

## Blockers

- None.

## Verification evidence

- `git status --short` showed only pre-existing untracked `fusion-second-opinion/docs/` and `fusion-second-opinion/references/` before this ledger was created.
- `git log --oneline --all -- claude-second-opinion gpt-second-opinion` identified the two likely behavioral commits above.
- `git show --word-diff 1448374` showed that the advisory rules survived unchanged in intent, while the new completion gate introduced the ambiguity and extra verification burden.
- `quick_validate.py` returned `Skill is valid!` for Claude, GPT, and Fusion.
- Each launch block extracted from its `## Run ... from the repository root` section passed `bash -n`.
- Focused invariant checks passed for the hard-stop language, process-versus-verdict distinction, critical-verdict completion rule, and prohibition on approval-seeking reruns.
- Marker simulation passed a critical `REVIEW STATUS: COMPLETE` result and rejected an unreadable-input `REVIEW STATUS: INCOMPLETE` result.
- Final `git diff --check` produced no errors.
- Post-clarification `quick_validate.py` returned `Skill is valid!` for all three skills.
- Post-clarification `bash -n` passed for all three embedded launch blocks.
- Focused assertions confirmed all three skills require rerun after loss of critical/load-bearing material while retaining the advisory/no-approval-loop rules.
- Post-clarification `git diff --check` produced no errors.
- Provider-routing validation confirmed the reciprocal Claude/GPT preference appears in both metadata and invocation policy.
- Fusion validation confirmed `User-invoked only`, generic-request rejection, autonomous-use prohibition, and high-stakes cost guidance, with no residual discretionary invocation language.
- Description lengths are 845 characters for Claude, 800 for GPT, and 784 for Fusion.
- Final `quick_validate.py`, `bash -n`, semantic assertions, and `git diff --check` all passed.
- Final terminology scan found no remaining `paid-credit` variants; `git diff --check` passed.

## Artifacts

- `claude-second-opinion/SKILL.md`
- `gpt-second-opinion/SKILL.md`
- `fusion-second-opinion/SKILL.md`
- `docs/second-opinion-skill-investigation.md`

## Single next action

- Stage the validated tracked changes for commit.
