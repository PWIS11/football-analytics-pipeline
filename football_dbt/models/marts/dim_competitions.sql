-- Dimension: one row per competition.
select distinct
    competition_code,
    competition_name as name
from {{ ref('stg_matches') }}
where competition_code is not null
