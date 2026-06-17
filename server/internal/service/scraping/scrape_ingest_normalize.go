package scraping

import (
	"errors"
	"fmt"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
)

func normalizeCourseRecord(course rawCoursePayload) (normalizedCourseRecord, error) {
	code := strings.TrimSpace(course.Code)
	name := strings.TrimSpace(course.Name)
	if code == "" || name == "" {
		code, name = splitCourseName(course.CourseName)
	}
	if code == "" {
		return normalizedCourseRecord{}, errors.New("course code is required")
	}
	level := extractCourseLevelNumber(code)
	return normalizedCourseRecord{
		Code:          code,
		Name:          name,
		Description:   strings.TrimSpace(course.Description),
		Restrictions:  strings.TrimSpace(course.Restrictions),
		Prerequisites: course.Prerequisites,
		Units:         parseUnits(course.Units),
		LevelNumber:   level,
	}, nil
}

func splitCourseName(courseName string) (string, string) {
	courseName = strings.TrimSpace(courseName)
	if courseName == "" {
		return "", ""
	}
	if code, title, ok := strings.Cut(courseName, " - "); ok {
		return strings.TrimSpace(code), strings.TrimSpace(title)
	}
	return "", courseName
}

var courseCodePattern = regexp.MustCompile(`\b([A-Z]{2,10}\s\d[A-Z0-9]{2,4}(?:\s+A/B)?)\b`)

func normalizeProgramRequirementCodes(requirements []string) []string {
	codes := make([]string, 0, len(requirements))
	seen := make(map[string]struct{}, len(requirements))
	for _, requirement := range requirements {
		match := courseCodePattern.FindStringSubmatch(strings.TrimSpace(requirement))
		if len(match) < 2 {
			continue
		}
		code := strings.TrimSpace(match[1])
		if _, ok := seen[code]; ok {
			continue
		}
		seen[code] = struct{}{}
		codes = append(codes, code)
	}
	return codes
}

func parseUnits(units string) int32 {
	match := regexp.MustCompile(`(\d+)`).FindStringSubmatch(units)
	if len(match) < 2 {
		return 0
	}
	var value int32
	_, _ = fmt.Sscanf(match[1], "%d", &value)
	return value
}

func extractCourseLevelNumber(courseCode string) *int32 {
	match := regexp.MustCompile(`\b[A-Z]{2,10}\s(\d)`).FindStringSubmatch(courseCode)
	if len(match) < 2 {
		return nil
	}
	var value int32
	_, _ = fmt.Sscanf(match[1], "%d", &value)
	return &value
}

func normalizeTerm(term string) string {
	term = strings.TrimSpace(term)
	if term == "" {
		return "Unknown"
	}
	match := regexp.MustCompile(`^(\d{4})\s+(.+)$`).FindStringSubmatch(term)
	if len(match) == 3 {
		return strings.TrimSpace(match[2]) + " " + match[1]
	}
	return term
}

func parseSectionName(raw string) (string, string) {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return "", ""
	}
	match := regexp.MustCompile(`^([A-Z0-9]+)\s*-\s*([A-Z]+)(?:\s+\(\d+\))?$`).FindStringSubmatch(strings.ToUpper(raw))
	if len(match) == 3 {
		return match[2] + " " + match[1], match[2]
	}
	parts := strings.Fields(raw)
	if len(parts) > 0 {
		return raw, strings.ToUpper(parts[0])
	}
	return raw, ""
}

func parseScrapeTime(value string) (string, error) {
	value = strings.TrimSpace(value)
	if value == "" || strings.EqualFold(value, "TBA") {
		return "", errors.New("time is empty")
	}
	for _, layout := range []string{"3:04PM", "3:04 PM"} {
		parsed, err := time.Parse(layout, value)
		if err == nil {
			return parsed.Format("15:04:05"), nil
		}
	}
	return "", fmt.Errorf("invalid time %q", value)
}

func parseNullableScrapeTime(value string) (pgtype.Time, error) {
	value = strings.TrimSpace(value)
	if value == "" || strings.EqualFold(value, "TBA") {
		return pgtype.Time{}, nil
	}
	normalized, err := parseScrapeTime(value)
	if err != nil {
		return pgtype.Time{}, err
	}
	parsed, err := time.Parse("15:04:05", normalized)
	if err != nil {
		return pgtype.Time{}, err
	}
	return pgtype.Time{
		Microseconds: int64(parsed.Hour()*3600+parsed.Minute()*60+parsed.Second()) * 1_000_000,
		Valid:        true,
	}, nil
}

func parseScrapeLocation(value string) (string, string) {
	raw := strings.TrimSpace(value)
	if raw == "" {
		return "", ""
	}
	upper := strings.ToUpper(raw)
	if upper == "IN PERSON" || upper == "IN-PERSON" {
		return "", ""
	}
	if strings.Contains(upper, "TBD") || strings.Contains(upper, "TBA") ||
		strings.Contains(upper, "ANNOUNCED") || strings.Contains(upper, "SEE CLASS NOTES") {
		return "TBD", "TBD"
	}
	if strings.Contains(upper, "ONLINE") || strings.Contains(upper, "VIRTUAL") {
		return "Online", "Online"
	}
	parts := strings.Fields(raw)
	if len(parts) >= 2 && regexp.MustCompile(`^[A-Z0-9]+$`).MatchString(parts[0]) {
		room := strings.TrimSpace(strings.Join(parts[1:], " "))
		room = strings.TrimSpace(regexp.MustCompile(`(?i)lab`).ReplaceAllString(room, ""))
		return parts[0], room
	}
	return raw, ""
}

func getInstructorNames(value string) []string {
	cleaned := strings.ReplaceAll(value, "\u00a0", " ")
	names := make([]string, 0)
	for _, line := range strings.Split(cleaned, "\n") {
		for _, part := range strings.Split(line, ",") {
			name := strings.Join(strings.Fields(part), " ")
			if name != "" {
				names = append(names, name)
			}
		}
	}
	return names
}

func getAllInstructorNames(section rawSectionPayload) []string {
	seen := make(map[string]struct{})
	for _, detail := range section.Details {
		for _, name := range getInstructorNames(detail.Instructor) {
			seen[name] = struct{}{}
		}
	}
	names := make([]string, 0, len(seen))
	for name := range seen {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

func getSectionInstructorSet(section rawSectionPayload) map[string]struct{} {
	names := make(map[string]struct{})
	for _, name := range getAllInstructorNames(section) {
		if !strings.EqualFold(name, "Staff") {
			names[name] = struct{}{}
		}
	}
	return names
}

func detectDeliveryMode(section rawSectionPayload) (string, bool) {
	hasOnline := false
	hasInPerson := false
	for _, detail := range section.Details {
		room := strings.ToUpper(strings.TrimSpace(detail.Room))
		switch {
		case strings.Contains(room, "ONLINE") || strings.Contains(room, "VIRTUAL"):
			hasOnline = true
		case room == "IN PERSON" || room == "IN-PERSON":
			hasInPerson = true
		case room != "" && room != "TBA" && room != "TBD":
			hasInPerson = true
		}
	}
	switch {
	case hasOnline && hasInPerson:
		return "Blended", true
	case hasOnline:
		return "Online", false
	case hasInPerson:
		return "In Person", true
	default:
		return "Unknown", false
	}
}

func buildSectionReferences(sections []normalizedSection) []sectionReference {
	// Build a name -> ID lookup for all sections.
	nameToID := make(map[string]int32, len(sections))
	for _, section := range sections {
		nameToID[section.Name] = section.ID
	}

	refs := make([]sectionReference, 0)
	for _, section := range sections {
		if section.ParentName == "" {
			continue
		}
		parentID, ok := nameToID[section.ParentName]
		if !ok {
			continue
		}
		refs = append(refs, sectionReference{ParentID: parentID, ChildID: section.ID})
	}
	return refs
}

func collectScheduleTeacherNames(schedules []rawScheduleCoursePayload) map[string]struct{} {
	names := make(map[string]struct{})
	for _, course := range schedules {
		for _, section := range course.Sections {
			for _, name := range getAllInstructorNames(section) {
				names[name] = struct{}{}
			}
		}
	}
	return names
}

func resolveScheduleCourseCode(course rawScheduleCoursePayload, titleCodeMap map[string]string) string {
	code := strings.TrimSpace(course.CourseCode)
	if courseCodePattern.MatchString(code) {
		return code
	}
	if resolved := titleCodeMap[strings.TrimSpace(course.CourseTitle)]; resolved != "" {
		return resolved
	}
	return code
}

func nonRMPID(name string) string {
	id := strings.ToLower(strings.TrimSpace(name))
	id = regexp.MustCompile(`\s+`).ReplaceAllString(id, "_")
	return "non_rmp_" + id
}

func nullableText(value string) pgtype.Text {
	value = strings.TrimSpace(value)
	if value == "" {
		return pgtype.Text{}
	}
	return pgtype.Text{String: value, Valid: true}
}

func numericFromFloat64(value float64) pgtype.Numeric {
	var numeric pgtype.Numeric
	_ = numeric.Scan(fmt.Sprintf("%g", value))
	return numeric
}
