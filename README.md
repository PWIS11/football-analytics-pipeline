# Football Analytics Pipeline

An end-to-end, reproducible **ELT** pipeline that ingests match data from a
public API, lands it in DuckDB, and models it into a tested star schema with
**dbt** — built to demonstrate analytics-engineering practice (ELT, dimensional
modelling, data quality testing, documentation, reproducibility).

> Data source: [football-data.org](https://www.football-data.org/) v4 API (free tier).

---

![2023/24 Premier League Title Race](data/processed/pl_race_2023.gif)

*2023/24 Premier League title race — cumulative points by game week. Generated
by [`scripts/animate_pl_race.py`](scripts/animate_pl_race.py) from the dbt mart.*

---

## Live Dashboard

> **View interactive Power BI dashboard** — link will be added after publish

Three pages — Season Race (bump chart), League Table, and League DNA (attack vs
defence quadrant) — covering 5 leagues across 2 seasons.

## Architecture

```mermaid
flowchart TD
    A["Public API<br/>football-data.org"] --> B["Python: extract<br/>rate-limited client"]
    B --> C["Python: load<br/>raw_matches in DuckDB"]
    C --> D["dbt: staging<br/>clean + type"]
    D --> E["dbt: marts<br/>star schema + tests + docs"]
    E --> F["Parquet outputs<br/>(external models)"]
    F --> G["Power BI<br/>dark-theme dashboard"]
    G --> H["Publish to web<br/>public dashboard"]
    E --> I["Matplotlib animation<br/>README chart"]
```

The split is deliberate: **Python only Extracts and Loads** the raw data, and
**dbt does all Transformation in SQL**. That is the ELT pattern — the same shape
a production analytics-engineering stack uses, scaled down to run free on a
laptop.

## Data model

A star schema, two aggregate facts, and a matchday-level standings history —
all built and tested by dbt.

```mermaid
erDiagram
    dim_teams ||--o{ fct_matches : "home / away"
    dim_competitions ||--o{ fct_matches : "competition_code"
    dim_seasons ||--o{ fct_matches : "season_id"
    dim_teams ||--o{ fct_team_season_stats : "team_id"
    dim_teams ||--o{ fct_standings_by_matchday : "team_id"
    fct_matches {
        bigint match_id PK
        date match_date
        bigint home_team_id FK
        bigint away_team_id FK
        int home_goals
        int away_goals
        int total_goals
        string winner
    }
    fct_team_season_stats {
        string competition_code
        bigint season_id
        bigint team_id FK
        int points
        int goal_difference
    }
    fct_standings_by_matchday {
        string competition_code
        bigint season_id
        int matchday
        bigint team_id FK
        int cumulative_points
        int position
    }
```

`fct_team_season_stats` is a league-table style aggregate: points, wins/draws/
losses and goal difference per team, per competition, per season.

`fct_standings_by_matchday` snapshots each team's cumulative points and league
position after every game week — the source of truth for the bump chart and the
animated README chart.

## Tech stack

| Layer         | Tool                            |
|---------------|---------------------------------|
| Extract       | Python, `requests`              |
| Load          | DuckDB (`raw_matches`)          |
| Transform     | **dbt** (`dbt-duckdb`)          |
| Testing       | `pytest` (EL) + dbt data tests  |
| Serving       | Parquet → Power BI              |
| Visualisation | Matplotlib (animated GIF)       |

## Project structure

```text
football-analytics-pipeline/
├── config.py              # competitions, seasons, paths, rate limit
├── pipeline.py            # EL: extract -> load raw_matches into DuckDB
├── src/
│   ├── extract.py         # rate-limited API client
│   ├── transform.py       # flatten nested JSON -> flat raw table
│   └── load.py            # write raw_matches into DuckDB
├── football_dbt/          # dbt project (the "T")
│   ├── dbt_project.yml
│   ├── profiles.yml       # local profile, points at the DuckDB file
│   └── models/
│       ├── staging/       # stg_matches (clean + type) + source/tests
│       └── marts/         # dim_*, fct_matches, fct_team_season_stats,
│                          # fct_standings_by_matchday + tests
├── scripts/
│   └── animate_pl_race.py # generate the README animated GIF
├── tests/
│   └── test_transform.py  # runs offline on sample data
└── data/
    ├── raw/               # raw API dumps (sample committed)
    └── processed/         # DuckDB + Parquet marts + animated GIF
```

## Quickstart

```bash
# 1. Clone and enter
git clone <your-repo-url> && cd football-analytics-pipeline

# 2. Create a virtual environment and install
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Add your API token
cp .env.example .env        # then paste your football-data.org token

# 4. Extract + Load: pull data and land it in DuckDB
python pipeline.py

# 5. Transform: build and test the models with dbt
cd football_dbt
dbt build --profiles-dir .          # staging -> marts + run all tests
dbt docs generate --profiles-dir .  # build the documentation site
dbt docs serve --profiles-dir .     # open the docs in your browser (optional)

# 6. Regenerate the animated README chart
cd ..
python scripts/animate_pl_race.py
```

No token yet? Rebuild everything from the committed sample with no network:

```bash
python pipeline.py --offline
pytest -q
cd football_dbt && dbt build --profiles-dir .
```

## Connecting Power BI

The marts are written as Parquet, which Power BI reads natively. Use the GitHub
raw URL as the data source so the published dashboard works for anyone:

```text
https://raw.githubusercontent.com/<your-user>/football-analytics-pipeline/main/data/processed/fct_standings_by_matchday.parquet
```

*Get Data → Web* and repeat for each mart, then wire the relationships on the
`*_id` keys. *File → Embed report → Publish to web (public)* gives a shareable
link with no Power BI login required.

## Roadmap

- [x] **Iteration 1 (MVP):** API → Python → Parquet/DuckDB → Power BI
- [x] **Iteration 2:** ELT refactor — Python lands raw data, `dbt-duckdb` owns
      transformation (staging → marts), with `unique` / `not_null` /
      `relationships` / `accepted_values` tests and auto-generated docs
- [x] **Iteration 3 (portfolio):** `fct_standings_by_matchday` model; animated
      title-race GIF in README; dark-theme Power BI dashboard (Season Race bump
      chart, League Table, League DNA quadrant)
- [ ] **Iteration 4:** scheduled refresh via GitHub Actions; incremental models;
      more competitions and cross-season comparison

## License

MIT
