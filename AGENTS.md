# RE:FOLD development and publication

- This task already has an isolated checkout. Work in the existing repository; do not create a worktree unless the user asks.
- This is a static, simulated front-end demo. Keep the existing collection, correction/undo, original album, simulated-save, similarity and localStorage behavior intact. Never embed credentials or connect a paid AI service without an explicit request.
- Use relative asset paths so the site works under `/ux/`. `index.html` is the entry point; `.nojekyll` keeps GitHub Pages serving the static files directly.
- The user has authorized publishing this demo from the `main` branch, repository root, to GitHub Pages. For future UI requests, finish and test the requested changes, then update the same site on `main` without a separate deployment confirmation. Preserve unrelated work and check the remote before pushing; do not force push.
- Before publishing, run `tests/test_ui.py` against a local server, check 375/390/430px mobile and 1440×900 desktop layouts, and inspect browser errors and missing assets. After publishing, verify the deployed URL and the main interactions.
- Keep the standalone `RE_FOLD_v06_Demo.html` in sync with `index.html`, `styles.css`, and assets when those change; it is an offline export, not the deployed entry point.
- Never commit `.env` files, authentication data, local backup archives, or the private design-reference screenshots in `references/`. The local legacy README is preserved but excluded from publication.
