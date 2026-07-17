---
name: policyengine-research-lookup
description: |
  Find and cite PolicyEngine's published blog posts and research articles as evidence or proof
  points — for talks, pitches, grant narratives, and "has PolicyEngine written about X?"
  Triggers: "find a blog post", "PolicyEngine research on", "published analysis", "proof point",
  "has PolicyEngine written about", "cite our work on", "which post covers", "blog post about".
metadata:
  category: process
---

# PolicyEngine research lookup

Find existing PolicyEngine articles to cite as evidence or to model tone against. PolicyEngine
has published ~185 articles — US and UK policy analyses, model/methodology notes, and org
announcements. Paths below are verified against the policyengine-app-v2 mirror.

## Where posts live

In policyengine-app-v2:

- **Article bodies** (plain markdown, some Jupyter `.ipynb`): `app/src/data/posts/articles/<filename>`
- **Post index** (title, description, date, tags, authors, image): `app/src/data/posts/posts.json`
- **Author records** (slug → name/bio): `app/src/data/posts/authors.json`

Article files are **plain markdown — metadata is not in per-file YAML frontmatter.** Each post's
title, date, tags, and authors live in `posts.json`, keyed to the article's `filename`; the
`authors` field holds slugs that resolve in `authors.json`. A `posts.json` entry:

```json
{
  "title": "How we used Claude Code to apply for the Public Benefit Innovation Fund",
  "description": "Treating writing as software development...",
  "date": "2025-08-28",
  "tags": ["us", "org", "ai", "featured"],
  "authors": ["max-ghenis"],
  "filename": "policyengine-atlas-pbif-grant.md",
  "image": "policyengine-atlas-demo.png"
}
```

A post's public URL is `policyengine.org/<country>/research/<filename-without-extension>`.

## Lookup recipes

```bash
POSTS=~/PolicyEngine/policyengine-app-v2/app/src/data/posts

# Full-text search article bodies for a topic
grep -rli "child tax credit" "$POSTS/articles/" | head

# Search titles/descriptions in the index
python3 -c 'import json;[print(p["date"],p["filename"]) for p in json.load(open("'"$POSTS"'/posts.json")) if "eitc" in (p["title"]+p.get("description","")).lower()]'

# Filter by tag (e.g. everything tagged "featured" or "uk")
python3 -c 'import json;[print(p["date"],p["title"]) for p in json.load(open("'"$POSTS"'/posts.json")) if "featured" in p.get("tags",[])]'

# Most recent posts
python3 -c 'import json;[print(p["date"],p["title"]) for p in sorted(json.load(open("'"$POSTS"'/posts.json")),key=lambda p:p["date"],reverse=True)[:10]]'
```

Prefer these recipes over any hardcoded list — the corpus changes weekly, so a static index of
filenames goes stale. Search live, then cite the exact filename and date you found.

## Frequently cited proof points

Verified filenames worth knowing (confirm current framing in the index before quoting):

| Topic | filename | Use for |
|---|---|---|
| UK government adoption | `policyengine-10-downing-street.md` | credibility, state capacity |
| US state tax coverage | `state-tax-model-beta.md` | federal + 50-state reach |
| Grant-writing with AI | `policyengine-atlas-pbif-grant.md` | tooling, org velocity |
| US federal proposals | `harris-ctc.md`, `harris-eitc.md` | CTC/EITC analysis depth |
| UK fiscal events | `autumn-budget-2024-employer-nic-pension-contributions.md` | budget/manifesto costing |

## Related skills

- **policyengine-writing** — match the tone and neutrality standard of published posts.
- **policyengine-us** / **policyengine-uk** — for "do we cover program/state X?" answer from the
  model, not just the blog.
