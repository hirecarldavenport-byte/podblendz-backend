-- =====================================================
-- Education & Learning Episode Selection (Phase 1)
-- Uses recency-first selection across known podcasts
-- Schema-aligned with podblendz.db
-- =====================================================

WITH ranked AS (
    SELECT
        e.id AS episode_id,
        e.podcast_id,
        e.title,
        e.published_at,

        -- Exponential recency decay (τ = 45 days)
        exp(
            -1.0 * (julianday('now') - julianday(e.published_at)) / 45.0
        ) AS recency_score,

        ROW_NUMBER() OVER (
            PARTITION BY e.podcast_id
            ORDER BY
                exp(
                    -1.0 * (julianday('now') - julianday(e.published_at)) / 45.0
                ) DESC
        ) AS row_num

    FROM episodes e
    WHERE e.podcast_id IN (
        'hidden_brain',
        '99_percent_invisible',
        'ted_talks_daily'
    )
)

SELECT
    episode_id,
    podcast_id,
    title,
    published_at,
    recency_score
FROM ranked
WHERE
    (podcast_id = 'hidden_brain' AND row_num <= 12)
 OR (podcast_id = '99_percent_invisible' AND row_num <= 10)
 OR (podcast_id = 'ted_talks_daily' AND row_num <= 10)
ORDER BY recency_score DESC;