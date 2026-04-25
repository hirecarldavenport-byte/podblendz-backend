-- select_education_learning_candidates.sql
-- Selects the best candidate episodes for transcription

WITH scored AS (
    SELECT
        s.episode_id,
        s.podcast_id,
        s.title,
        s.description,
        s.published_at,
        s.topic_score,

        -- recency decay
        exp(-1.0 * (julianday('now') - julianday(s.published_at)) / 45.0)
            AS recency_score,

        -- final relevance score
        (0.6 * s.topic_score)
        +
        (0.4 * exp(-1.0 * (julianday('now') - julianday(s.published_at)) / 45.0))
            AS relevance

    FROM (
        SELECT * FROM episodes
        WHERE master_topic = 'education_learning'
    ) s
),

ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY podcast_id
               ORDER BY relevance DESC
           ) AS row_num
    FROM scored
    WHERE relevance >= 0.30
)

SELECT *
FROM ranked
WHERE
    (podcast_id = 'hidden_brain' AND row_num <= 10)
 OR (podcast_id = '99_percent_invisible' AND row_num <= 8)
 OR (podcast_id = 'ted_talks_daily' AND row_num <= 8)
ORDER BY relevance DESC;