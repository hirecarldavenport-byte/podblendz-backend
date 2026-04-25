-- select_education_learning_candidates.sql
-- Title-based candidate selection for initial transcription pass
-- Aligned with current episodes schema (podblendz.db)

WITH scored AS (
    SELECT
        e.id AS episode_id,
        e.podcast_id,
        e.title,
        e.published_at,

        (
          -- Environment / systems / design
          CASE WHEN lower(e.title) LIKE '%design%'
            OR lower(e.title) LIKE '%environment%'
            OR lower(e.title) LIKE '%context%'
            OR lower(e.title) LIKE '%system%'
          THEN 1 ELSE 0 END

          +

          -- Habits / change / patterns
          CASE WHEN lower(e.title) LIKE '%habit%'
            OR lower(e.title) LIKE '%change%'
            OR lower(e.title) LIKE '%pattern%'
            OR lower(e.title) LIKE '%routine%'
          THEN 1 ELSE 0 END

          +

          -- Cognition / mind / attention
          CASE WHEN lower(e.title) LIKE '%mind%'
            OR lower(e.title) LIKE '%brain%'
            OR lower(e.title) LIKE '%attention%'
            OR lower(e.title) LIKE '%thinking%'
          THEN 1 ELSE 0 END

          +

          -- Decisions / framing questions
          CASE WHEN lower(e.title) LIKE '%decision%'
            OR lower(e.title) LIKE '%choice%'
            OR lower(e.title) LIKE '%why%'
            OR lower(e.title) LIKE '%how%'
          THEN 1 ELSE 0 END
        ) / 4.0 AS topic_score,

        exp(
          -1.0 * (julianday('now') - julianday(e.published_at)) / 45.0
        ) AS recency_score

    FROM episodes e
    WHERE e.podcast_id IN (
        'hidden_brain',
        '99_percent_invisible',
        'ted_talks_daily'
    )
),

ranked AS (
    SELECT *,
           (0.6 * topic_score + 0.4 * recency_score) AS relevance,
           ROW_NUMBER() OVER (
               PARTITION BY podcast_id
               ORDER BY (0.6 * topic_score + 0.4 * recency_score) DESC
           ) AS row_num
    FROM scored
    -- IMPORTANT: relaxed gate for first exploratory pass
    WHERE topic_score >= 0
)

SELECT
    episode_id,
    podcast_id,
    title,
    published_at,
    relevance
FROM ranked
WHERE
    (podcast_id = 'hidden_brain' AND row_num <= 10)
 OR (podcast_id = '99_percent_invisible' AND row_num <= 8)
 OR (podcast_id = 'ted_talks_daily' AND row_num <= 8)
ORDER BY relevance DESC;