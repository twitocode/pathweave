-- name: GetPlans :many
SELECT p.*, COUNT(pc.course_id) as course_count
FROM plan p
LEFT JOIN plan_course pc ON p.id = pc.plan_id
WHERE p.user_id = @user_id
GROUP BY p.id;

-- name: CreatePlan :one
INSERT INTO plan (title, term, user_id) VALUES (@title, @term, @user_id)
RETURNING id;

-- name: GetPlanInfo :one
SELECT 
  p.id, p.title, p.term, p.created_at, p.updated_at, p.user_id,
  (
    SELECT COALESCE(
      JSON_AGG(
        JSON_BUILD_OBJECT(
          'id', pc.id,
          'course_id', c.id,
          'code', c.code,
          'name', c.name,
          'description', c.description,
          'restrictions', c.restrictions,
          'prerequisites', c.prerequisites,
          'units', c.units,
          'types', (
            SELECT COALESCE(JSON_AGG(t.type), '[]'::json)
            FROM (
              SELECT DISTINCT type
              FROM section s_inner
              WHERE s_inner.course_id = c.id
            ) t
          ),
          'teachers', (
            SELECT COALESCE(
              JSON_AGG(
                JSON_BUILD_OBJECT(
                  'id', t.id,
                  'name', t.name,
                  'avg_rating', t.avg_rating,
                  'avg_difficulty', t.avg_difficulty,
                  'department', t.department,
                  'rmp_id', t.rmp_id,
                  'num_ratings', t.num_ratings
                )
              ), 
              '[]'::json
            )
            FROM (
              SELECT teacher.id, teacher.name, teacher.avg_rating, teacher.avg_difficulty, teacher.department, teacher.rmp_id, teacher.num_ratings
              FROM course_teachers ct
              JOIN teacher ON teacher.id = ct.teacher_id
              WHERE ct.course_id = c.id
            ) t
          ),
          'sections', (
            SELECT COALESCE(
              JSON_AGG(
                JSON_BUILD_OBJECT(
                  'id', s.id,
                  'name', s.name,
                  'type', s.type,
                  'term', s.term,
                  'mode', s.mode,
                  'is_in_person', s.is_in_person,
                  'class_number', s.class_number,
                  'meetings', (
                    SELECT COALESCE(
                      JSON_AGG(
                        JSON_BUILD_OBJECT(
                          'id', sm.id,
                          'days', sm.days,
                          'start_time', sm.start_time,
                          'end_time', sm.end_time,
                          'building', sm.building,
                          'room', sm.room
                        )
                      ), 
                      '[]'::json
                    )
                    FROM section_meeting sm
                    WHERE sm.section_id = s.id
                  ),
                  'teachers', (
                    SELECT COALESCE(
                      JSON_AGG(
                        JSON_BUILD_OBJECT(
                          'id', teacher.id,
                          'name', teacher.name,
                          'avg_rating', teacher.avg_rating,
                          'avg_difficulty', teacher.avg_difficulty,
                          'department', teacher.department,
                          'rmp_id', teacher.rmp_id,
                          'num_ratings', teacher.num_ratings
                        )
                      ), 
                      '[]'::json
                    )
                    FROM section_teachers st
                    JOIN teacher ON teacher.id = st.teacher_id
                    WHERE st.section_id = s.id
                  )
                )
              ),
              '[]'::json
            )
            FROM plan_section ps
            JOIN section s ON s.id = ps.section_id
            WHERE ps.plan_course_id = pc.id
          )
        )
      ), 
      '[]'::json
    )
    FROM plan_course pc
    JOIN course c ON c.id = pc.course_id
    WHERE pc.plan_id = p.id
  )::json AS courses
FROM plan p
WHERE p.id = @plan_id::UUID AND p.user_id = @user_id::UUID;