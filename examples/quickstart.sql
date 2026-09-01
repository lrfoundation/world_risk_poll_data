-- Quickstart: World Risk Poll data in SQL, via DuckDB.
--
-- DuckDB queries the Parquet files directly -- no load/import step and
-- no database file needed. Run from the repository root:
--   duckdb < examples/quickstart.sql
-- or, inside an interactive `duckdb` session:
--   .read examples/quickstart.sql
--
-- Requires: DuckDB (https://duckdb.org/docs/installation/)

-- 1. Load a single wave --------------------------------------------------

SELECT count(*) AS respondents
FROM   read_parquet('WRP_2025/WRP_2025.parquet');

-- Within-country weighted average worry score for 2025, over respondents
-- who have a worry_score (it is null for anyone who skipped an item).
SELECT round(sum(worry_score * WGT) / sum(WGT), 3) AS worry_score_2025
FROM   read_parquet('WRP_2025/WRP_2025.parquet')
WHERE  worry_score IS NOT NULL;

-- 2. Stack all four waves for a trend ------------------------------------
-- union_by_name matches columns by name across the four files, which is
-- exactly what the 37-variable harmonised block (docs/CODEBOOK.md) is
-- for: matching names, codes and labels in every wave.

CREATE OR REPLACE VIEW trend AS
SELECT *
FROM   read_parquet(
         ['WRP_2019/WRP_2019.parquet', 'WRP_2021/WRP_2021.parquet',
          'WRP_2023/WRP_2023.parquet', 'WRP_2025/WRP_2025.parquet'],
         union_by_name = true
       );

-- Global worry_score by year, weighted by PROJWT (a population weight,
-- appropriate here because the trend is pooled across countries -- use
-- WGT instead for a within-country-only comparison).
SELECT Year,
       round(sum(worry_score * PROJWT) / sum(PROJWT), 3) AS worry_score
FROM   trend
WHERE  worry_score IS NOT NULL
GROUP BY Year
ORDER BY Year;

-- 3. A wave-specific question, trended by hand ---------------------------
-- "Climate change is a threat to [country] in the next 20 years" is
-- asked in every wave but sits outside the harmonised block, under a
-- different variable name each time: L5 in 2019, WP20719 from 2021 on.
-- 1 = very serious threat, 2 = somewhat serious, 3 = not a threat;
-- 98/99 are DK/refused and excluded below. This is the general pattern
-- for trending any comparable question that isn't in the harmonised
-- block: alias it to one name per wave, then UNION ALL.

CREATE OR REPLACE VIEW climate_threat AS
SELECT Year, PROJWT, L5 AS climate_threat
FROM   read_parquet('WRP_2019/WRP_2019.parquet')
WHERE  L5 IN (1, 2, 3)
UNION ALL
SELECT Year, PROJWT, WP20719 AS climate_threat
FROM   read_parquet('WRP_2021/WRP_2021.parquet')
WHERE  WP20719 IN (1, 2, 3)
UNION ALL
SELECT Year, PROJWT, WP20719 AS climate_threat
FROM   read_parquet('WRP_2023/WRP_2023.parquet')
WHERE  WP20719 IN (1, 2, 3)
UNION ALL
SELECT Year, PROJWT, WP20719 AS climate_threat
FROM   read_parquet('WRP_2025/WRP_2025.parquet')
WHERE  WP20719 IN (1, 2, 3);

-- % who see climate change as at least a somewhat serious threat, by
-- year, weighted by PROJWT.
SELECT Year,
       round(100 * sum(PROJWT) FILTER (WHERE climate_threat IN (1, 2))
                 / sum(PROJWT), 1) AS pct_serious_threat
FROM   climate_threat
GROUP BY Year
ORDER BY Year;
