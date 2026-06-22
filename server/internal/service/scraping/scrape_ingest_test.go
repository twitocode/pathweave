package scraping

import (
	"testing"

	"github.com/stretchr/testify/require"
)

func TestScrapeIngestNormalizeCourseRecord(t *testing.T) {
	record, err := normalizeCourseRecord(rawCoursePayload{
		CourseName:    "COMPSCI 1DM3 - Discrete Mathematics for Computer Science",
		Units:         "3 unit(s)",
		Description:   "Sets and logic",
		Restrictions:  "Antirequisite(s): MATH 1DM3",
		Prerequisites: []string{"MATH 1ZA3"},
	})
	require.NoError(t, err)
	require.Equal(t, "COMPSCI 1DM3", record.Code)
	require.Equal(t, "Discrete Mathematics for Computer Science", record.Name)
	require.Equal(t, int32(3), record.Units)
	require.NotNil(t, record.LevelNumber)
	require.Equal(t, int32(1), *record.LevelNumber)
}

func TestScrapeIngestParseMeetingDetails(t *testing.T) {
	start, err := parseScrapeTime("4:30PM")
	require.NoError(t, err)
	require.Equal(t, "16:30:00", start)

	building, room := parseScrapeLocation("BSB B156")
	require.Equal(t, "BSB", building)
	require.Equal(t, "B156", room)

	building, room = parseScrapeLocation("Online")
	require.Equal(t, "Online", building)
	require.Equal(t, "Online", room)
}

func TestScrapeIngestBuildSectionReferences(t *testing.T) {
	sections := []normalizedSection{
		{ID: 1, Name: "LEC C01", Type: "LEC", ParentNames: []string{""}, InstructorSet: map[string]struct{}{"Jane Doe": {}}},
		{ID: 2, Name: "LAB L01", Type: "LAB", ParentNames: []string{"LEC C01"}, InstructorSet: map[string]struct{}{"Jane Doe": {}}},
		{ID: 3, Name: "TUT T01", Type: "TUT", ParentNames: []string{"LEC C01"}, InstructorSet: map[string]struct{}{}},
		{ID: 4, Name: "LAB L02", Type: "LAB", ParentNames: []string{""}, InstructorSet: map[string]struct{}{"Other Person": {}}},
	}

	refs := buildSectionReferences(sections)
	require.Len(t, refs, 2)
	require.Equal(t, sectionReference{ParentID: 1, ChildID: 2}, refs[0])
	require.Equal(t, sectionReference{ParentID: 1, ChildID: 3}, refs[1])
}
