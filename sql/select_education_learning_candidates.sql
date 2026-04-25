(
  CASE WHEN lower(e.title) LIKE '%design%'
    OR lower(e.title) LIKE '%environment%'
    OR lower(e.title) LIKE '%context%'
    OR lower(e.title) LIKE '%system%'
  THEN 1 ELSE 0 END

  +

  CASE WHEN lower(e.title) LIKE '%change%'
    OR lower(e.title) LIKE '%habit%'
    OR lower(e.title) LIKE '%pattern%'
    OR lower(e.title) LIKE '%routine%'
  THEN 1 ELSE 0 END

  +

  CASE WHEN lower(e.title) LIKE '%mind%'
    OR lower(e.title) LIKE '%brain%'
    OR lower(e.title) LIKE '%attention%'
    OR lower(e.title) LIKE '%thinking%'
  THEN 1 ELSE 0 END

  +

  CASE WHEN lower(e.title) LIKE '%choice%'
    OR lower(e.title) LIKE '%decision%'
    OR lower(e.title) LIKE '%why%'
    OR lower(e.title) LIKE '%how%'
  THEN 1 ELSE 0 END
) / 4.0 AS topic_score