package common

import (
	"strconv"
	"time"
)

func AppendYearToTerm(term *string) string {
	year := time.Now().Year()
	if *term != "Fall" {
		year += 1
	}
	return *term + " " + strconv.Itoa(year)
}

var ValidTerms []string = []string{"2269", "2271", "2275"}

var TermNumberToString = map[string]string{
	"2259": "Fall 2025",
	"2261": "Winter 2026",
	"2265": "Spring/Summer 2026",
	"2269": "Fall 2026",
	"2271": "Winter 2027",
	"2275": "Spring/Summer 2027",
}
