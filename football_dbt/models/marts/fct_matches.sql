-- Fact: one row per match, with foreign keys and derived measures.
select
    match_id,
    match_date,
    kickoff_utc,
    matchday,
    status,
    competition_code,
    season_id,
    home_team_id,
    away_team_id,
    home_goals,
    away_goals,
    ht_home_goals,
    ht_away_goals,
    winner,
    home_goals + away_goals as total_goals,
    home_goals - away_goals as goal_difference
from {{ ref('stg_matches') }}
