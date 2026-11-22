> `SKILL.md` devamı — parça 7/7. Bağlam: # /graphify

## For /graphify add and --watch

Neither is part of the default build. When the user runs `/graphify add <url>` to fetch a URL into the corpus, or passes `--watch` to auto-rebuild on file changes, see `references/add-watch.md`.

---

## For the commit hook and native CLAUDE.md integration

When the user asks to install the post-commit auto-rebuild hook or wire graphify into a project's CLAUDE.md, see `references/hooks.md`.

---

## Troubleshooting

### PowerShell 5.1: Vertical scrolling stops working

If vertical scrolling breaks in PowerShell after running graphify, this is caused by ANSI escape sequences from the `graspologic` library. Graphify v0.3.10+ suppresses this output, but if you still see the issue:

1. **Upgrade graphify**: `pip install --upgrade graphifyy`
2. **Use Windows Terminal** instead of the legacy PowerShell console — Windows Terminal handles ANSI codes correctly
3. **Reset your terminal**: close and reopen PowerShell
4. **Skip Leiden**: uninstall its backend (`pip uninstall graspologic` on Python < 3.13, `pip uninstall graspologic-native` on Python 3.13+) and graphify will fall back to NetworkX's built-in Louvain algorithm, which produces no ANSI output

---

## Honesty Rules

- Never invent an edge. If unsure, use AMBIGUOUS.
- Never skip the corpus check warning.
- Always show token cost in the report.
- Never hide cohesion scores behind symbols - show the raw number.
- Never run HTML viz on a graph with more than 5,000 nodes without warning the user.
