# Claremont School IT Help

Static IT help site rebuilt from the public Google Site content.

## Local preview

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Regenerate migrated content

The migration script crawls the public Google Site navigation and rebuilds article pages, category pages, and the search index.

```powershell
python scripts\build_site.py
```

## Publishing

The site is plain static HTML/CSS/JS and is suitable for GitHub Pages. Add a `CNAME` file when the final custom domain is chosen.
