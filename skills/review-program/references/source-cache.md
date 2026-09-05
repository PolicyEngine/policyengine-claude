# Shared source evidence

Encoding and review share original documents through `--sources MANIFEST`. This saves
acquisition and rendering work; it does not certify any interpretation of the source.
Use a JSON manifest with this shape (replace example paths/hashes with actual values):

```json
{
  "version": 1,
  "worktree_root": "/absolute/current/worktree",
  "sources": [
    {
      "url": "https://agency.example/manual.pdf",
      "path": "/tmp/policyengine-command-runs/WORKTREE_ID/program-source-1.pdf",
      "sha256": "actual SHA-256 of the original file",
      "text": {
        "path": "/tmp/policyengine-command-runs/WORKTREE_ID/program-source-1.txt",
        "source_sha256": "actual SHA-256 of the original file",
        "sha256": "actual SHA-256 of the extract"
      },
      "renders": [
        {
          "page": 8,
          "dpi": 300,
          "source_sha256": "actual SHA-256 of the original file",
          "path": "/tmp/policyengine-command-runs/WORKTREE_ID/program-source-1-page-8.png",
          "sha256": "actual SHA-256 of this image"
        }
      ]
    }
  ]
}
```

Each original requires URL, absolute path and checksum. `text` and `renders` are
optional; HTML extracts and spreadsheets may be originals too. Record only derivatives
actually produced from those original bytes; each derivative's `source_sha256` binds it
to that version of the original. Preserve physical PDF page boundaries when
extracting text. Missing screenshots are normal; do not fabricate a full page sequence.
For user-supplied or merged packets, retain the supplied file's identity and add an
optional `provenance` description with original URLs and packet-page mappings where
known. Do not present an assembled packet as a byte-identical download of one URL;
unknown provenance is an evidence limitation, not something to invent.

Keep the manifest and files under this worktree's `RUN_ROOT` or its local `sources/`. Copy user-provided
files there before registering them. Never adopt another worktree's cache. Record the
original URL without a PDF `#page=N` fragment, and reuse the same original for multiple
cited pages. Preserve HTML hash routes (for example `#page/FAA6/...`), which identify
different content. A fresh source response with different bytes is a new version: invalidate its
derivatives and findings that depend on it. A checksum proves unchanged bytes, not legal
authority, date applicability, currentness or completeness; reviewers still check those.

Run the bundled helper once before handing reusable evidence to a reviewer (resolve the
script relative to the installed review-program skill):

```bash
python3 "$REVIEW_SKILL_ROOT/scripts/check_source_manifest.py" \
  --manifest "$SOURCE_MANIFEST" --worktree-root "$WORKTREE_ROOT" --run-root "$RUN_ROOT" \
  > "$RUN_ROOT/${PREFIX}-review-source-cache-check.json"
```

It returns validated `sources`, rejected originals and discarded derivatives. A rejected
original cannot support a cached finding. Regenerate a discarded derivative only when
needed; reuse its valid original. The helper checks local integrity without fetching or
writing evidence. It exits unsuccessfully for a malformed manifest or wrong worktree;
continue with fresh acquisition, within the source budget, or report the missing evidence.

The policy reviewer writes the updated `{PREFIX}-review-sources.json`; an encoder's
document collector writes `{PREFIX}-sources.json`. Do not edit the supplied manifest in
place. A later review can pass the prior review's source manifest via the same flag.
