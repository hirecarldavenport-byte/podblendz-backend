-- episode_seed_relevance.sql
-- Computes a normalized topic relevance score (0.0–1.0)
-- for environment, habits, cognition, and decision-making

SELECT
    e.*,

    (
        CASE
            WHEN lower(e.title || ' ' || e.description) LIKE '%environment%'
              OR lower(e.title || ' ' || e.description) LIKE '%context%'
              OR lower(e.title || ' ' || e.description) LIKE '%design%'
              OR lower(e.title || ' ' || e.description) LIKE '%defaults%'
              OR lower(e.title || ' ' || e.description) LIKE '%systems%'
            THEN 1 ELSE 0
        END

        +

        CASE
            WHEN lower(e.title || ' ' || e.description) LIKE '%habit%'
              OR lower(e.title || ' ' || e.description) LIKE '%routine%'
              OR lower(e.title || ' ' || e.description) LIKE '%behavior%'
              OR lower(e.title || ' ' || e.description) LIKE '%pattern%'
            THEN 1 ELSE 0
        END

        +

        CASE
            WHEN lower(e.title || ' ' || e.description) LIKE '%cognition%'
              OR lower(e.title || ' ' || e.description) LIKE '%attention%'
              OR lower(e.title || ' ' || e.description) LIKE '%focus%'
              OR lower(e.title || ' ' || e.description) LIKE '%thinking%'
            THEN 1 ELSE 0
        END

        +

        CASE
            WHEN lower(e.title || ' ' || e.description) LIKE '%decision%'
              OR lower(e.title || ' ' || e.description) LIKE '%choice%'
              OR lower(e.title || ' ' || e.description) LIKE '%bias%'
              OR lower(e.title || ' ' || e.description) LIKE '%judgment%'
            THEN 1 ELSE 0
        END
    ) / 4.0 AS topic_score

FROM episodes e
WHERE e.master_topic = 'education_learning';