# TechNewsDaily RSS

This repository is configured to publish a simple static site via GitHub Pages.

What I added:

- `docs/index.html` — a minimal homepage that will be served.
- `docs/.nojekyll` — prevents GitHub Pages from ignoring files that start with an underscore.
- `.github/workflows/pages.yml` — a GitHub Actions workflow that deploys `docs/` to Pages on every push to `main`.

How to use:

1. Edit or replace files in the `docs/` folder with your site.
2. Commit and push to `main` — the workflow will run and publish the site.
3. In the repository Settings → Pages, ensure the site is configured to use GitHub Actions (the workflow handles the deployment).

Optional:

- Add a `CNAME` file to `docs/` to set a custom domain.
- If you want Pages to be served from `gh-pages` branch instead, remove `docs/` and update the workflow accordingly.
