# A2RT documentation site

This directory adapts the Sphinx theme from `proteinseek/proteinseek-workbench-docs`
at commit `27e632de8ada413b8255921535e839a2bb16c0bc`. See the repository's
`THIRD_PARTY_NOTICES.md` for provenance.

Run the integrated build from the repository root:

```sh
python scripts/build.py
```

Outputs are `dist/docs/zh/` and `dist/docs/en/`. `dist/docs/index.html` is the
language landing page. Chinese Core chapters are generated from `protocol/`.
Edit the introductory pages in `source/zh/` and English guides in `source/en/`.

`conf.py` receives the public website configuration from the build. It contains
no model credentials. When `DOCS_AI_ENDPOINT` and `TURNSTILE_SITE_KEY` are empty,
the theme exposes local documentation search only. See `../DEPLOY.md` to enable
the Worker-backed AI interface.

The build also creates a JSON index from the rendered documentation. The Worker
reads that exact index; it does not require a separate ChromaDB process.
