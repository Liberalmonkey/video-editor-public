# graphify reference: incremental update and cluster-only

Load this only when the user passed `--update` or `--cluster-only`. A first-time full build never reads this file.

## For --update (incremental re-extraction)

Use when you've added or modified files since the last run. Only re-extracts changed files - saves tokens and time.

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.detect import detect_incremental, save_manifest
from pathlib import Path

from graphify.paths import out_path
from graphify.watch import _read_build_excludes, _read_build_gitignore
result = detect_incremental(Path('INPUT_PATH'), extra_excludes=_read_build_excludes(out_path()), gitignore=_read_build_gitignore(out_path()))
new_total = result.get('new_total', 0)
nf = result.get('new_files', {})
print(json.dumps({
    'new_total': new_total,
    'deleted': len(result.get('deleted_files', [])),
    'new_by_type': {t: len(v) for t, v in nf.items()},
    'total_files': result.get('total_files'),
    'total_words': result.get('total_words'),
    'skipped_sensitive': result.get('skipped_sensitive', []),
}, indent=2, ensure_ascii=False))
print('Full result: graphify-out/.graphify_incremental.json')
Path('graphify-out/.graphify_incremental.json').write_text(json.dumps(result, ensure_ascii=False), encoding=\"utf-8\")
deleted = list(result.get('deleted_files', []))
if new_total == 0 and not deleted:
    print('No files changed since last run. Nothing to update.')
    raise SystemExit(0)
if deleted:
    print(f'{len(deleted)} deleted file(s) to prune.')
if new_total > 0:
    print(f'{new_total} new/changed file(s) to re-extract.')
"
```

Then populate `.graphify_detect.json` so Steps 3A–6 (which read it unconditionally) see the right state for an incremental run. `files` carries the changed subset (drives Step 3A AST + Step 3B0 cache check on only what changed); `all_files` carries the full corpus for any step that needs corpus-wide context:

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
r = json.loads(Path('graphify-out/.graphify_incremental.json').read_text(encoding=\"utf-8\"))
Path('graphify-out/.graphify_detect.json').write_text(json.dumps({
    'files': r.get('new_files', {}),
    'all_files': r.get('files', {}),
    'total_files': r.get('new_total', 0),
    'total_words': r.get('total_words', 0),
    'skipped_sensitive': r.get('skipped_sensitive', []),
    'needs_graph': True,
}, ensure_ascii=False), encoding=\"utf-8\")
"
```

If new files exist, first check whether all changed files are code files:

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path

result = json.loads(open('graphify-out/.graphify_incremental.json', encoding='utf-8').read()) if Path('graphify-out/.graphify_incremental.json').exists() else {}
code_exts = {'.py','.ts','.js','.go','.rs','.java','.cpp','.c','.rb','.swift','.kt','.cs','.scala','.php','.cc','.cxx','.hpp','.h','.kts','.lua','.toc','.f','.F','.f90','.F90','.f95','.F95','.f03','.F03','.f08','.F08'}
new_files = result.get('new_files', {})
all_changed = [f for files in new_files.values() for f in files]
code_only = all(Path(f).suffix.lower() in code_exts for f in all_changed)
print('code_only:', code_only)
"
```

If `code_only` is True: print `[graphify update] Code-only changes detected - skipping semantic extraction (no LLM needed)`, run Step 3A (AST) on the changed files, then follow only Part B's **Fast path** to overwrite `.graphify_semantic.json` with an empty result and run Part C to create `.graphify_extract.json` from the fresh AST result. Skip semantic cache checks/writes and subagents (Steps B0–B3); do not reuse semantic sidecars from a prior run. Continue to the incremental merge and Steps 4–8 only after Part C has completed.

If `code_only` is False (any changed file is a doc/paper/image/video): **first, if any changed file is in `new_files['video']`, run `references/transcribe.md` (Step 2.5) on those files, then rewrite `.graphify_detect.json` to move the resulting transcript paths into `files['document']` and drop `files['video']`** — otherwise raw `.mp4/.mp3` paths are fed to semantic subagents as unreadable media (#1392). Then run the full Steps 3A–3C pipeline as normal.

If no new files exist (only deletions), create an empty extraction so the merge step can prune:

```bash
if [ ! -f graphify-out/.graphify_extract.json ]; then
    echo '[graphify update] Only deletions -- creating empty extraction for merge.'
    $(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
Path('graphify-out/.graphify_extract.json').write_text(json.dumps({'nodes':[],'edges':[],'hyperedges':[],'input_tokens':0,'output_tokens':0}), encoding='utf-8')
"
fi
```


## Devamı (ayrı dosyalar)
Bu dosya 150 satır sınırı için bölündü; içerik sırayla şu parçalarda sürer:
- [update.part2.md](update.part2.md): For --cluster-only
