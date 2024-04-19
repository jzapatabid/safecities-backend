class Queries:
    CUSTOM_INITIATIVE_LIST = """
    SELECT sub.* FROM
    (
        SELECT DISTINCT
            i.id AS initiative_id,
            i.name AS initiative_name,
            exists(select 1 from initiative_prioritization ip where ip.initiative_id = i.id) as prioritized,
            i.justification as justification,
            i.evidences as evidences,
            i.cost_level  AS cost_level,
            i.efficiency_level  AS efficiency_level,

            (
                CASE WHEN i.is_default 
                THEN
                (
                    SELECT count(distinct icpa.cause_id) 
					FROM initiative_cause_problem_association icpa
					INNER JOIN
					cause_problem_association cpa
					ON
					icpa.cause_id = cpa.cause_id
					AND
					icpa.problem_id = cpa.problem_id
					join 
					problem p 
					on
					p.id = icpa.problem_id 
					WHERE 
					p.prioritized = true 
					and
					cpa.prioritized = true 
					and
					icpa.initiative_id = i.id
                )
                ELSE 
                (
					SELECT count(distinct cpa.cause_id) 
					FROM initiative_cause_association ica
					INNER JOIN
					cause_problem_association cpa
					ON
					ica.cause_id = cpa.cause_id
					join 
					problem p 
					on
					p.id = cpa.problem_id 
					WHERE 
					p.prioritized = true 
					and
					cpa.prioritized = true 
					and
					ica.initiative_id = i.id
                )
                END
            ) AS total_cause_count,
                
            (
                CASE WHEN i.is_default 
                THEN
                (
                    SELECT count(DISTINCT icpa.problem_id)
					FROM initiative_cause_problem_association icpa
					INNER JOIN
					cause_problem_association cpa
					ON
					icpa.cause_id = cpa.cause_id
					AND
					icpa.problem_id = cpa.problem_id                    
					join 
					problem p 
					on
					p.id = icpa.problem_id 
					WHERE 
					p.prioritized = true 
					and
					cpa.prioritized = true 
					and
					icpa.initiative_id = i.id
                )
                ELSE 
                (
                    SELECT count(DISTINCT cpa.problem_id)
					FROM initiative_cause_association ica
					INNER JOIN
					cause_problem_association cpa
					ON
					ica.cause_id = cpa.cause_id                  
					join 
					problem p 
					on
					p.id = cpa.problem_id 
					WHERE 
					p.prioritized = true 
					and
					cpa.prioritized = true 
					and
					ica.initiative_id = i.id
                )
                END                     
            ) AS total_problem_count

		FROM initiative AS i
		WHERE id IN 
		(
		SELECT i.id
		FROM initiative AS i
		INNER JOIN
		initiative_cause_problem_association AS icpa
		ON 
		icpa.initiative_id = i.id
		INNER JOIN
		cause_problem_association AS cpa
		ON
		cpa.cause_id = icpa.cause_id
		AND
		cpa.problem_id = icpa.problem_id
		WHERE 
		cpa.prioritized = true
		UNION 
		SELECT DISTINCT initiative_id 
		FROM initiative_cause_association ica 
		WHERE cause_id IN (
			SELECT DISTINCT cause_id
			FROM cause_problem_association cpa 
			WHERE prioritized = true 
			)
			
		)
	) sub
    WHERE
    NOT (sub.total_problem_count = 0 AND sub.total_cause_count = 0)
    ORDER BY :orderfield :sorttype
    LIMIT :limitt OFFSET :offsett
    """

    TOTAL_INITIATIVE_ELEMENTS = """
    SELECT COUNT(*) AS total_items 
    FROM
    (
        SELECT DISTINCT
            i.id AS initiative_id,
			(
		    CASE WHEN i.is_default 
                THEN
                (
                    SELECT count(DISTINCT icpa.cause_id)
                    FROM initiative_cause_problem_association icpa
					join
					problem p
					on
					p.id = icpa.problem_id
                    WHERE p.prioritized = true
					AND icpa.initiative_id = i.id
                )
                ELSE 
                (
                    SELECT count(DISTINCT ica.cause_id)
                    FROM initiative_cause_association ica
					INNER JOIN
					cause_problem_association cpa
					ON
					ica.cause_id = cpa.cause_id
					join
					problem p
					on p.id = cpa.problem_id
                    WHERE p.prioritized = true
					AND ica.initiative_id = i.id
                )
                END
            ) AS total_cause_count,
                
            (
                CASE WHEN i.is_default 
                THEN
                (
                    SELECT count(DISTINCT icpa.problem_id)
                    FROM initiative_cause_problem_association icpa
                	join
					problem p
					on
					p.id = icpa.problem_id
                    WHERE p.prioritized = true
                    AND icpa.initiative_id = i.id
                )
                ELSE 
                (
                    SELECT count(DISTINCT cpa.problem_id)
                    FROM initiative_cause_association ica
                    LEFT JOIN cause_problem_association cpa
                    ON ica.cause_id = cpa.cause_id
					join
					problem p
					on cpa.problem_id = p.id
                    WHERE p.prioritized = true
                    AND ica.initiative_id = i.id
                )
                END                     
            ) AS total_problem_count

		FROM initiative AS i
		WHERE id IN 
		(
		SELECT i.id
		FROM initiative AS i
		INNER JOIN
		initiative_cause_problem_association AS icpa
		ON 
		icpa.initiative_id = i.id
		INNER JOIN
		cause_problem_association AS cpa
		ON
		cpa.cause_id = icpa.cause_id
		AND
		cpa.problem_id = icpa.problem_id
		WHERE 
		cpa.prioritized = true
		UNION 
		SELECT DISTINCT initiative_id 
		FROM initiative_cause_association ica 
		WHERE cause_id IN (
			SELECT DISTINCT cause_id
			FROM cause_problem_association cpa 
			WHERE prioritized = true 
			) 
		)
	) sub
    WHERE
    NOT (sub.total_problem_count = 0 AND sub.total_cause_count = 0)
    """
