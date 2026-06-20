-- Dimension: one row per season.
select distinct
    season_id,
    season_start_date as start_date,
    season_end_date   as end_date,
    extract(year from season_start_date) as start_year
from {{ ref('stg_matches') }}
where season_id is not null
