-- Cumulative standings after each matchday: points, goals, and league position.
-- Powers the Power BI "Season Race" bump chart and the animated README chart.

with finished as (
    select * from {{ ref('stg_matches') }}
    where status = 'FINISHED'
      and home_goals is not null
      and away_goals is not null
),

team_match as (
    select
        competition_code, season_id, matchday,
        home_team_id                                         as team_id,
        case when home_goals > away_goals then 3
             when home_goals = away_goals then 1 else 0 end  as points,
        home_goals                                           as goals_for,
        away_goals                                           as goals_against
    from finished

    union all

    select
        competition_code, season_id, matchday,
        away_team_id                                         as team_id,
        case when away_goals > home_goals then 3
             when away_goals = home_goals then 1 else 0 end  as points,
        away_goals                                           as goals_for,
        home_goals                                           as goals_against
    from finished
),

per_matchday as (
    select
        competition_code,
        season_id,
        matchday,
        team_id,
        sum(points)        as points_this_matchday,
        sum(goals_for)     as goals_for_this_matchday,
        sum(goals_against) as goals_against_this_matchday
    from team_match
    group by 1, 2, 3, 4
),

cumulative as (
    select
        competition_code,
        season_id,
        matchday,
        team_id,
        sum(points_this_matchday) over (
            partition by competition_code, season_id, team_id
            order by matchday
            rows between unbounded preceding and current row
        ) as cumulative_points,
        sum(goals_for_this_matchday) over (
            partition by competition_code, season_id, team_id
            order by matchday
            rows between unbounded preceding and current row
        ) as cumulative_goals_for,
        sum(goals_against_this_matchday) over (
            partition by competition_code, season_id, team_id
            order by matchday
            rows between unbounded preceding and current row
        ) as cumulative_goals_against
    from per_matchday
)

select
    competition_code,
    season_id,
    matchday,
    team_id,
    cumulative_points,
    cumulative_goals_for,
    cumulative_goals_against,
    cumulative_goals_for - cumulative_goals_against as cumulative_goal_difference,
    rank() over (
        partition by competition_code, season_id, matchday
        order by
            cumulative_points desc,
            (cumulative_goals_for - cumulative_goals_against) desc,
            cumulative_goals_for desc
    ) as position
from cumulative
