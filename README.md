# ai-data-hunter

**AI Data Hunter** — tell it what data you need; it discovers, extracts,
normalizes, deduplicates and validates. This module is the extraction/normalize
core (pure stdlib; the fetcher is pluggable so it works with Firecrawl,
Playwright, or a mock). Handles messy prices (`$89.99`, `89,99 MAD`,
`1.234,50 €`), deduplicates by source+name fingerprint, and validates against
schema rules.

> Original project, aligned with the "AI Web Scraping / Data Hunter" trend.

## Usage

```python
from data_hunter import Record, hunt

def my_fetcher(url: str) -> list:
    # integrate Firecrawl / Playwright here
    return [Record("shop", "Red Shoe", 50.0, url)]

clean = hunt(my_fetcher, ["https://shop-a", "https://shop-b"])
```

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).

---

## Links

- 🌐 Website: [huggehub.com](https://www.huggehub.com)
- 💻 GitHub: [@astrodevit-creator](https://github.com/astrodevit-creator)
- 🔗 LinkedIn: [El Badaoui Hatim](https://www.linkedin.com/in/el-badaoui-hatim-it)
