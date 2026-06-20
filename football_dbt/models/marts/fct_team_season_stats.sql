-- Fact (aggregate): league-table style stats per team, per competition, per season.
-- Each finished match contributes two rows (home + away perspective), then we
-- aggregate to one row per team-season.

with finished as (
    select * from {{ ref('stg_matches') }}
    where status = 'FINISHED' and home_goals is not null and away_goals is not null
),

team_match as (
    -- home perspective
    select
        competition_code, season_id,
        home_team_id as team_id,
        home_goals   as goals_for,
        away_goals   as goals_against,
        case when home_goals > away_goals then 3
             when home_goals = away_goals then 1 else 0 end as points,
        case when home_goals > away_goals then 1 else 0 end as is_win,
        case when home_goals = away_goals then 1 else 0 end as is_draw,
        case when home_goals < away_goals then 1 else 0 end as is_loss
    from finished

    union all

    -- away perspective
    select
        competition_code, season_id,
        away_team_id as team_id,
        away_goals   as goals_for,
        home_goals   as goals_against,
        case when away_goals > home_goals then 3
             when away_goals = home_goals then 1 else 0 end as points,
        case when away_goals > home_goals then 1 else 0 end as is_win,
        case when away_goals = home_goals then 1 else 0 end as is_draw,
        case when away_goals < home_goals then 1 else 0 end as is_loss
    from finished
)

select
    competition_code,
    season_id,
    team_id,
    count(*)                            as matches_played,
    sum(is_win)                         as wins,
    sum(is_draw)                        as draws,
    sum(is_loss)                        as losses,
    sum(goals_for)                      as goals_for,
    sum(goals_against)                  as goals_against,
    sum(goals_for) - sum(goals_against) as goal_difference,
    sum(points)                         as points
from team_match
group by 1, 2, 3
