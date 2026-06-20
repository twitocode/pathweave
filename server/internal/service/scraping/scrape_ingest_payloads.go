package scraping

import (
	"encoding/json"

	"github.com/google/uuid"
)

type CreateScrapeRunRequest struct {
	Source   string          `json:"source"`
	Metadata json.RawMessage `json:"metadata"`
}

type StageScrapeArtifactsRequest struct {
	Courses   []rawCoursePayload       `json:"courses"`
	Programs  []rawProgramPayload      `json:"programs"`
	Teachers  []rawTeacherPayload      `json:"teachers"`
	Schedules []rawScheduleTermPayload `json:"schedules"`
}

type StageScrapeArtifactsResult struct {
	RunID             uuid.UUID `json:"run_id"`
	CourseCount       int       `json:"course_count"`
	ProgramCount      int       `json:"program_count"`
	TeacherCount      int       `json:"teacher_count"`
	ScheduleTermCount int       `json:"schedule_term_count"`
}

type PromoteScrapeRunResult struct {
	RunID    uuid.UUID `json:"run_id"`
	Status   string    `json:"status"`
	Promoted bool      `json:"promoted"`
}

type rawCoursePayload struct {
	Code          string   `json:"code"`
	Name          string   `json:"name"`
	CourseName    string   `json:"course_name"`
	Units         string   `json:"units"`
	Description   string   `json:"description"`
	Restrictions  string   `json:"restrictions"`
	Prerequisites []string `json:"prerequisites"`
}

type rawProgramPayload struct {
	ProgramName         string          `json:"program_name"`
	URL                 string          `json:"url"`
	Requirements        []string        `json:"requirements"`
	RequirementsByLevel json.RawMessage `json:"requirements_by_level"`
}

type rawTeacherPayload struct {
	ID            string   `json:"id"`
	Name          string   `json:"name"`
	AvgRating     float64  `json:"avgRating"`
	AvgDifficulty float64  `json:"avgDifficulty"`
	Department    string   `json:"department"`
	NumRatings    int32    `json:"numRatings"`
	Courses       []string `json:"courses"`
}

type rawScheduleTermPayload struct {
	Term    string                     `json:"term"`
	Courses []rawScheduleCoursePayload `json:"courses"`
}

type rawScheduleCoursePayload struct {
	CourseCode  string              `json:"course_code"`
	CourseTitle string              `json:"course_title"`
	Term        string              `json:"term"`
	Sections    []rawSectionPayload `json:"sections"`
}

type rawSectionPayload struct {
	SectionName string              `json:"section_name"`
	Parent      string              `json:"parent"`
	ClassNumber int16               `json:"class_number"`
	Details     []rawMeetingPayload `json:"details"`
}

type rawMeetingPayload struct {
	Days       string `json:"days"`
	StartTime  string `json:"start_time"`
	EndTime    string `json:"end_time"`
	Room       string `json:"room"`
	Instructor string `json:"instructor"`
}

type normalizedCourseRecord struct {
	Code          string
	Name          string
	Description   string
	Restrictions  string
	Prerequisites []string
	Units         int32
	LevelNumber   *int32
}

type normalizedSection struct {
	ID            int32
	Name          string
	Type          string
	ParentName    string
	InstructorSet map[string]struct{}
}

type sectionReference struct {
	ParentID int32
	ChildID  int32
}
