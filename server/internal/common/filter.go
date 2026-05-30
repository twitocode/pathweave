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

var ValidTerms []string = []string{"Fall 2026", "Winter 2027", "Spring/Summer 2027"}
