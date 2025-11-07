# TechNewsDaily RSS

[Github Page](https://bookaitech.github.io/technewsdaily-rss/)

This repository is configured to publish a simple static site via GitHub Pages.

What I added:

- `docs/index.html` — a minimal homepage that will be served.
- `docs/.nojekyll` — prevents GitHub Pages from ignoring files that start with an underscore.
- `.github/workflows/pages.yml` — a GitHub Actions workflow that deploys `docs/` to Pages on every push to `main`.

New: RSS feed support

- `data/posts.json` — a simple JSON file containing feed items (title/link/description/pubDate/guid).
- `scripts/generate_feed.py` — generates `docs/feed.xml` (RSS 2.0) from `data/posts.json` using the Python standard library.
- `.github/workflows/generate-feed.yml` — action that runs the generator on every push and commits `docs/feed.xml` back to the repository if it changed.

Feed discovery

The site header now contains a discovery link to the feed so browsers and readers can find it automatically:
<link rel="alternate" type="application/rss+xml" title="TechNewsDaily RSS" href="feed.xml" />

How to add/update feed items

1. Edit `data/posts.json` and add items. Each item should include `title`, `link`, `description`, `pubDate` (ISO 8601), and optionally `guid`.
2. Run the generator locally to produce `docs/feed.xml`:

```bash
# from repo root
python3 scripts/generate_feed.py
```

3. Commit and push. The included GitHub Action will also regenerate and commit `docs/feed.xml` on push.

Where to find the feed

After publish, your feed will be available at `https://<your-username>.github.io/<repo>/feed.xml` (GitHub Pages serves the `docs/` folder). Many feed readers will also discover the feed automatically through the link in `docs/index.html`.

How to use:

1. Edit or replace files in the `docs/` folder with your site.
2. Commit and push to `main` — the workflow will run and publish the site.
3. In the repository Settings → Pages, ensure the site is configured to use GitHub Actions (the workflow handles the deployment).

Optional:

- Add a `CNAME` file to `docs/` to set a custom domain.
- If you want Pages to be served from `gh-pages` branch instead, remove `docs/` and update the workflow accordingly.
