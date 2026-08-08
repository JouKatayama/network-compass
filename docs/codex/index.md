# Codex Workflow

OpenAI Codex can use repository `AGENTS.md` instructions; this repo therefore keeps the root AGENTS file concise and places durable product/architecture knowledge in structured docs.

Use:

- `issue-prompt-template.md` for normal issues
- `NC-001-execution-prompt.md` for the first implementation
- `review-gates.md` for human/architect checkpoints

Codex should plan first, implement the smallest coherent issue, run checks, and report acceptance criteria. Do not ask it to "build Network Compass" as one task.
