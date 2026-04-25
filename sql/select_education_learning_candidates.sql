-- Select candidate education/learning episodes based on title-only signals
-- Schema-aligned with current episodes table

WITH scored AS (
    SELECT
        e.id AS episode_id,
        e.podcast_id,
        e.title,
        e.published_at,

        (
          CASE WHEN lower(e.title) LIKE '%environment%'
            OR lower(e.title) LIKE '%design%'
            OR lower(e.title) LIKE '%system%'
          THEN 1 ELSE 0 END

          +

          CASE WHEN lower(e.title) LIKE '%habit%'
            OR lower(e.title) LIKE '%routine%'
            OR lower(e.title) LIKE '%behavior%'
          THEN 1 ELSE 0 END

          +

          CASE WHEN lower(e.title) LIKE '%cognition%'
            OR lower(e.title) LIKE '%attention%'
            OR lower(e.title) LIKE '%focus%'
            OR lower(e.title) LIKE '%thinking%'
          THEN 1 ELSE 0 END

          +

          CASE WHEN lower(e.title) LIKE '%decision%'
            OR lower(e.title) LIKE '%choice%'
            OR lower(e.title) LIKE '%bias%'
            OR lower(e.title) LIKE '%judgment%'
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
    WHERE topic_score > 0
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