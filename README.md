# realtorIQ buyer’s guide

[Open the live report](https://krisitown.github.io/realtoriq-buyers-guide/)

A self-contained, interactive report covering Dragalevtsi and seven comparison neighbourhoods in southern Sofia. It includes asking-price distributions, neighbourhood benchmarks, a budget explorer, a comparable-property price check, source listing links, and shortlist CSV export.

## Data and interpretation

The report uses the **22 October 2026** collection snapshot: 3,739 sale advertisements in the selected areas, tentatively grouped into 2,169 ad groups. Collection ended with gaps on every source. These are **asking prices**, not completed transactions or verified valuations. Duplicate groups are estimates, not confirmed unique properties. The full screening, grouping and statistical methodology is documented inside the report.

Advertiser descriptions and links are included as source evidence. Their claims and present availability have not been independently verified. Third-party listing content remains attributable to its respective sources.

## Local use and publication

Open `index.html` in a browser. No build step, dependencies, external chart libraries or server is required.

GitHub Pages publishes the repository root from the default branch. To update the report, replace `index.html` with a freshly verified report and commit the change. The website is a frozen snapshot and does not run or monitor crawlers.

Crawler code, raw collection files, credentials and local workspace configuration are intentionally not included. The classification CSV contains source identifiers, basic listing metadata and short evidence excerpts, not the full raw crawl.

## Construction stage and furnishing classification

Updated **25 October 2026**, using the original 22 October snapshot. A lightweight Luna agent designed and audited reproducible Bulgarian text rules, applied to **all 15,569 captured source records** (sale and rent). This is agent-assisted rule-based extraction, not a separate model review or legal verification of every property.

- Construction: `green`, `act14`, `act15`, `act16`, `unknown`, `conflict`, `not_applicable`.
- Furnishing, independently: `furnished`, `partial`, `unfurnished`, `unknown`, `conflict`.
- Expected/future stages and payment milestones are not treated as achieved stages. Unclear evidence remains unknown.
- Duplicate groups retain source evidence; disagreeing non-unknown labels become conflicting claims.
- Stage/furnishing filters update the price benchmarks, budget counts and price checker. Segment medians require at least eight eligible groups. They do not measure the causal value of construction stage or furniture.

[Download all-source classifications](property-classifications.csv). The export contains one row per captured source URL, including rentals and areas outside the buyer report. The report's interactive shortlist remains sale-only in the eight selected neighbourhoods. See `classification-summary.json` for source fingerprint and full-data counts.

Most source records do not provide decisive stage/furnishing evidence. Read those unknowns as missing information, not proof of early construction or an unfurnished home. Labels can be wrong when ad prose is ambiguous, hypothetical, contradictory or describes several properties. Source claims still need verification.

### Reproduce the text classification

With Python 3 and the original source JSONL supplied locally:

```sh
python3 tools/classify_properties.py /path/to/sofia-latest.jsonl --outdir classifications
python3 -m unittest discover -s tools -p test_classify_properties.py
```

Each input record is an object containing `provider` and `listing`, with `listing.originalUrl`, `listing.title` and `listing.description`. Reproduction does not fetch listings or update the published report automatically.
