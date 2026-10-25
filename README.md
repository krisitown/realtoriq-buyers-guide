# realtorIQ buyer’s guide

[Open the live report](https://krisitown.github.io/realtoriq-buyers-guide/)

A self-contained, interactive report covering Dragalevtsi and seven comparison neighbourhoods in southern Sofia. It includes asking-price distributions, neighbourhood benchmarks, a budget explorer, a comparable-property price check, source listing links, and shortlist CSV export.

## Data and interpretation

The report pools captures from **22–25 October 2026**: 4,221 sale advertisements in the selected areas, tentatively grouped into 2,469 ad groups. The expanded Sofia export contains 16,051 source records. Collection remains partial. These are **asking prices**, not completed transactions or verified valuations. Duplicate groups are estimates, not confirmed unique properties. The full screening, grouping and statistical methodology is documented inside the report.

Advertiser descriptions and links are included as source evidence. Their claims and present availability have not been independently verified. Third-party listing content remains attributable to its respective sources.

## Local use and publication

Open `index.html` in a browser. No build step, dependencies, external chart libraries or server is required.

GitHub Pages publishes the repository root from the default branch. To update the report, replace `index.html` with a freshly verified report and commit the change. The website is a frozen snapshot and does not run or monitor crawlers.

Crawler code, raw collection files, credentials and local workspace configuration are intentionally not included. The classification CSV contains source identifiers, basic listing metadata and short evidence excerpts, not the full raw crawl.

## Construction stage and furnishing classification

Updated **25 October 2026**, using the expanded pooled snapshot. A lightweight Luna agent designed and audited reproducible Bulgarian text rules, applied to **all 16,051 captured source records** (sale and rent). This is agent-assisted rule-based extraction, not a separate model review or legal verification of every property.

- Construction: `green`, `act14`, `act15`, `act16`, `unknown`, `conflict`, `not_applicable`.
- Furnishing, independently: `furnished`, `partial`, `unfurnished`, `unknown`, `conflict`.
- Expected/future stages and payment milestones are not treated as achieved stages. Unclear evidence remains unknown.
- Duplicate groups retain source evidence; disagreeing non-unknown labels become conflicting claims.
- One combined property-status selector updates the price benchmarks, budget counts and price checker. Segment medians require at least eight eligible groups. They do not measure the causal value of construction stage or furniture.

[Download all-source classifications](property-classifications.csv). The export contains one row per captured source URL, including rentals and areas outside the buyer report. The report's interactive shortlist remains sale-only in the eight selected neighbourhoods. See `classification-summary.json` for source fingerprint and full-data counts.

Most source records do not provide decisive stage/furnishing evidence. Read those unknowns as missing information, not proof of early construction or an unfurnished home. Labels can be wrong when ad prose is ambiguous, hypothetical, contradictory or describes several properties. Source claims still need verification.

### Reproduce the text classification

With Python 3 and the original source JSONL supplied locally:

```sh
python3 tools/classify_properties.py /path/to/sofia-latest.jsonl --outdir classifications
python3 -m unittest discover -s tools -p test_classify_properties.py
```

Each input record is an object containing `provider` and `listing`, with `listing.originalUrl`, `listing.title` and `listing.description`. Reproduction does not fetch listings or update the published report automatically.

## Combined buyer status and sample visibility

The report presents one status selector: early stages, Act 16 with explicit furnishing subgroups, furnished with an unconfirmed act, unstated stage, and needs-review cases. Act 14/15 or green listings with furnishing claims are flagged for review; the interface never promotes furniture alone to Act 16. “Act 16 — all” is a convenience filter over the Act 16 furnishing groups.

The selector shows current sample counts and disables empty options. The stage-sample comparison shows selected-area counts alongside the same property type across all eight areas. Wider-area and all-type controls help explore inventory. All-type mode withholds price benchmarks to avoid mixing houses, apartments and land.

The full CSV includes the original source-stage/furnishing labels plus `buyerStatus` and `buyerStatusLabel`. The combined rules are in `tools/property_status.py`. Classifier v2 corrects false stage exclusions from unrelated future wording and filters furniture claims about shared amenities or illustrative renderings. These remain text-derived, unverified claims.

## Dataset expansion — 25 October 2026

Fresh targeted crawls on Imot.bg, Holmes.bg and Imoti.com captured 940 sale ads across all eight comparison areas: 482 previously missing source URLs and 458 refreshed existing records. Each source used neighbourhood searches; Imot and Holmes also searched specifically for Dragalevtsi two-room apartments. All three runs finished without crawler failures. General searches were deliberately limited to three pages in Dragalevtsi and one in each other district, so the collection is not exhaustive. The Imot two-room search reached its terminal page; Holmes had more pages beyond its three-page budget.

Dragalevtsi tentative ad groups increased from **105 to 295**, and its two-room sample from **28 to 126**. Across all eight areas, groups increased from **2,169 to 2,469**. Counts describe advertisements and approximate duplicate groups, not verified unique available properties.

The merge keeps the newest capture per provider/source URL. Older unrefreshed ads are retained and may no longer be available. Individual source capture dates appear beside report links; dates describe capture, not initial publication. [Collection summary and coverage limits](collection-summary.json) record the expansion.
