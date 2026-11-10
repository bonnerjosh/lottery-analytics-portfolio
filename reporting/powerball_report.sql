-- Replace PROJECT_ID and DATASET_ID before running this query.
CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.powerball_report` AS
SELECT
  draw_date,
  EXTRACT(YEAR FROM draw_date) AS draw_year,
  game_type,
  CASE game_type
    WHEN 'POWERBALL' THEN 'Powerball'
    WHEN 'POWERBALL_DP' THEN 'Double Play'
    ELSE COALESCE(game_type, 'Unknown')
  END AS game_name,
  FORMAT('%02d %02d %02d %02d %02d', ball1, ball2, ball3, ball4, ball5) AS white_balls,
  powerball,
  multiplier,
  COUNT(*) OVER (PARTITION BY draw_date, game_type) > 1 AS duplicate_draw_key,
  CASE
    WHEN game_type = 'POWERBALL' THEN multiplier IS NULL OR multiplier NOT IN (1, 2, 3, 4, 5, 10)
    WHEN game_type = 'POWERBALL_DP' THEN multiplier IS NOT NULL
    ELSE TRUE
  END AS invalid_multiplier
FROM `PROJECT_ID.DATASET_ID.powerball`;
