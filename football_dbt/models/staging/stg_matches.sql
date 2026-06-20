-- Staging: clean, type, and rename the raw match data.
-- One row per match. No business logic beyond casting and tidying.

with source as (

    select * from {{ source('raw', 'raw_matches') }}

)

select
    cast(match_id as bigint)                  as match_id,
    cast(utc_date as timestamp)               as kickoff_utc,
    cast(utc_date as date)                    as match_date,
    matchday,
    status,
    stage,

    -- competition
    competition_code,
    competition_name,

    -- season
    cast(season_id as bigint)                 as season_id,
    cast(season_start_date as date)           as season_start_date,
    cast(season_end_date as date)             as season_end_date,

    -- teams
    cast(home_team_id as bigint)              as home_team_id,
    home_team_name,
    home_team_short_name,
    home_team_tla,
    home_team_crest,
    cast(away_team_id as bigint)              as away_team_id,
    away_team_name,
    away_team_short_name,
    away_team_tla,
    away_team_crest,

    -- score
    cast(home_goals as integer)               as home_goals,
    cast(away_goals as integer)               as away_goals,
    cast(ht_home_goals as integer)            as ht_home_goals,
    cast(ht_away_goals as integer)            as ht_away_goals,
    winner

from source
