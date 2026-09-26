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

## Jev (Vercel AI Gateway) record gating

`jev.py` calls [Jev](https://vercel.com/docs/ai-gateway/modalities/evaluation)
(`typesafe-ai/jev`) through Vercel AI Gateway to make fast yes/no judgments on
records. It needs no extra packages, only your gateway key in the environment:

```bash
cp .env.example .env   # then fill in AI_GATEWAY_API_KEY=your_key (git-ignored)
```

```python
from jev import jev_filter

kept, uncertain = jev_filter(clean, "Is this a real, purchasable product listing?")
```

Records with p >= 0.8 are kept, p <= 0.2 are dropped, and anything in between
comes back in `uncertain` so you can review it.

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
