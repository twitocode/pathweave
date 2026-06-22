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
	RunID             uuid.UUID `json:"runId"`
	CourseCount       int       `json:"courseCount"`
	ProgramCount      int       `json:"programCount"`
	TeacherCount      int       `json:"teacherCount"`
	ScheduleTermCount int       `json:"scheduleTermCount"`
}

type PromoteScrapeRunResult struct {
	RunID    uuid.UUID `json:"runId"`
	Status   string    `json:"status"`
	Promoted bool      `json:"promoted"`
}

type rawCoursePayload struct {
	Code          string   `json:"code"`
	Name          string   `json:"name"`
	CourseName    string   `json:"courseName"`
	Units         string   `json:"units"`
	Description   string   `json:"description"`
	Restrictions  string   `json:"restrictions"`
	Prerequisites []string `json:"prerequisites"`
}

type rawProgramPayload struct {
	ProgramName         string          `json:"programName"`
	URL                 string          `json:"url"`
	Requirements        []string        `json:"requirements"`
	RequirementsByLevel json.RawMessage `json:"requirementsByLevel"`
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
	CourseCode  string              `json:"courseCode"`
	CourseTitle string              `json:"courseTitle"`
	Term        string              `json:"term"`
	Sections    []rawSectionPayload `json:"sections"`
}

type rawSectionPayload struct {
	SectionName string              `json:"sectionName"`
	Parents     []string            `json:"parents"`
	ClassNumber int16               `json:"classNumber"`
	Details     []rawMeetingPayload `json:"details"`
}

type rawMeetingPayload struct {
	Days       string `json:"days"`
	StartTime  string `json:"startTime"`
	EndTime    string `json:"endTime"`
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
	ParentNames   []string
	InstructorSet map[string]struct{}
}

type sectionReference struct {
	ParentID int32
	ChildID  int32
}
