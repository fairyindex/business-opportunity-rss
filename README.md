# Lightweight Business Opportunity RSS Monitor

This public repository collects new items from a small set of RSS/Atom sources and writes a daily Markdown digest to [feeds.md](feeds.md).

## What it does

- Reads one feed URL per line from [feed-sources.txt](feed-sources.txt).
- Keeps items published in the last seven days, deduplicates by original URL, and sorts newest first.
- Records feed failures in the digest rather than hiding them.
- Runs daily through GitHub Actions and can also be run manually from the Actions page.

The digest is a discovery aid. RSS dates and descriptions should be checked against the original post before being used in a report.

## Sources

The initial set includes Side Hustle Nation, My Wife Quit Her Job, ezindie, Hacker News Show, Product Hunt, and three Reddit communities. Reddit may rate-limit anonymous requests; the daily status table will show failures.

To add or remove a source, edit `feed-sources.txt`, one URL per line. Do not put credentials, private URLs, or personal data in this public repository.

## Schedule

GitHub Actions runs at 00:00 UTC daily (08:00 China Standard Time / 09:00 Korea Standard Time). It also runs after changes are pushed to the default branch so the first digest is generated promptly.
