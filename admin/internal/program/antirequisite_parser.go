package program

import (
	"regexp"
	"strings"
)

// courseCodeRe matches a full course code like "ANTHROP 3HI3" or "COMPSCI 1JC3"
var antireqCourseCodeRe = regexp.MustCompile(`[A-Z]{2,}\s+\d[A-Z0-9]{2,4}`)

// shortCodeRe matches a bare course number like "3Z03" (inherits previous department)
var antireqShortCodeRe = regexp.MustCompile(`^\d[A-Z]{1,3}\d{1,2}$`)

// stopPhrases indicate the end of the antirequisite list and start of other restriction text
var antireqStopPhrases = []string{
	"Not open to",
	"This course",
	"Cross-list",
	"Priority",
	"It is recommended",
	"The Department",
	"May be repeated",
	"can be taken",
}

// ParseAntirequisites extracts course codes from a restrictions text field.
// It handles formats like:
//   - "Antirequisite(s): ANTHROP 3HI3, 3Z03 and 3ZZ3"       → [ANTHROP 3HI3, ANTHROP 3Z03, ANTHROP 3ZZ3]
//   - "Antirequisite(s): CMTYENGA 4B06 , INSPIRE 4B06"       → [CMTYENGA 4B06, INSPIRE 4B06]
//   - "Antirequisite(s): IBEHS 3EE6 A/B, 4E06 A/B"           → [IBEHS 3EE6, IBEHS 4E06]
//   - "Antirequisite(s): LABRST 1C03; LABRST 1E03"           → [LABRST 1C03, LABRST 1E03]
func ParseAntirequisites(restrictions string) []string {
	seen := make(map[string]bool)
	var codes []string

	lines := strings.Split(restrictions, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)

		idx := strings.Index(strings.ToLower(line), "antirequisite(s):")
		if idx == -1 {
			continue
		}

		after := line[idx+len("antirequisite(s):"):]

		for _, stop := range antireqStopPhrases {
			if si := strings.Index(after, stop); si != -1 {
				after = after[:si]
			}
		}

		parsed := parseCodesFromSegment(after)
		for _, code := range parsed {
			if !seen[code] {
				seen[code] = true
				codes = append(codes, code)
			}
		}
	}

	return codes
}

func parseCodesFromSegment(segment string) []string {
	var codes []string
	currentDept := ""

	segment = strings.ReplaceAll(segment, ";", ",")
	segment = strings.ReplaceAll(segment, " and ", ",")

	parts := strings.Split(segment, ",")

	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}

		part = strings.TrimSpace(strings.ReplaceAll(part, "A/B", ""))

		match := antireqCourseCodeRe.FindString(part)
		if match != "" {
			fields := strings.Fields(match)
			if len(fields) == 2 {
				currentDept = fields[0]
				code := currentDept + " " + fields[1]
				codes = append(codes, code)
			}
			continue
		}

		tokens := strings.Fields(part)
		if len(tokens) > 0 && antireqShortCodeRe.MatchString(tokens[0]) && currentDept != "" {
			code := currentDept + " " + tokens[0]
			codes = append(codes, code)
		}
	}

	return codes
}
