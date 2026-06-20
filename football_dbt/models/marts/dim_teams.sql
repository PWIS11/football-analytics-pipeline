-- Dimension: one row per team (appearing as home or away).

with home as (
    select home_team_id as team_id, home_team_name as name,
           home_team_short_name as short_name, home_team_tla as tla,
           home_team_crest as crest
    from {{ ref('stg_matches') }}
),
away as (
    select away_team_id as team_id, away_team_name as name,
           away_team_short_name as short_name, away_team_tla as tla,
           away_team_crest as crest
    from {{ ref('stg_matches') }}
),
unioned as (
    select * from home
    union
    select * from away
)
select distinct team_id, name, short_name, tla, crest
from unioned
where team_id is not null
