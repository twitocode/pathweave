package scraper

import (
	"errors"
	"log"
	neturl "net/url"
	"os"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly"
)

var (
	// Older catalog HTML used hideCatalogData on href="#".
	hideCatalogArgs = regexp.MustCompile(`hideCatalogData\s*\(\s*'(\d+)'\s*,\s*'\d+'\s*,\s*'(\d+)'`)
	showCourseArgs  = regexp.MustCompile(`showCourse\s*\(\s*'(\d+)'\s*,\s*'(\d+)'`)

	portfolioOnclick = regexp.MustCompile(`acalogPopup\('portfolio\.php\?([^']+)'`)
)

const (
	calendarHost      = "academiccalendars.romcmaster.ca"
	listingCatalogOID = "58"
	listingNavOID     = "12627"
)

type Course struct {
	PageURL       string
	CatOID        string
	COID          string
	PortfolioURL  string // favourites popup target (href is javascript:); empty if missing
	Name          string
	Prerequisites []string // linked course codes inside <em><a>…
	Description   string
}

func squashSpaces(s string) string {
	return strings.Join(strings.Fields(s), " ")
}

func isPreviewNOPOP(u *neturl.URL) bool {
	return u != nil && strings.HasSuffix(strings.ToLower(u.Path), "preview_course_nopop.php")
}

func pathLooksLikeCatalogContentPHP(path string) bool {
	lp := strings.ToLower(strings.TrimSpace(path))
	lp = strings.TrimSuffix(lp, "/")
	return lp == "/content.php" || lp == "content.php" || strings.HasSuffix(lp, "/content.php")
}

// isListingPaginationURL is true for course-index pagination (?filter[cpage]=…) on our listing.
func isListingPaginationURL(u *neturl.URL) bool {
	if u == nil || strings.ToLower(u.Hostname()) != calendarHost {
		return false
	}
	if !pathLooksLikeCatalogContentPHP(u.Path) {
		return false
	}
	q := u.Query()
	if q.Get("catoid") != listingCatalogOID || q.Get("navoid") != listingNavOID {
		return false
	}
	if q.Get("filter[cpage]") == "" {
		return false
	}
	// Ignore print/expand/contract variants; these are not pagination pages and
	// produce many extra requests + timeouts.
	if q.Has("print") || q.Has("expand") || q.Has("contract") || q.Has("display_location") {
		return false
	}
	if q.Has("coid[0]") {
		return false
	}
	return true
}

func isListingContentPage(u *neturl.URL) bool {
	return u != nil && strings.ToLower(u.Hostname()) == calendarHost && pathLooksLikeCatalogContentPHP(u.Path)
}

func GetAllCourses() []Course {
	c := colly.NewCollector(
		// Default colly UA is often blocked by catalog backends; mimic a browser.
		colly.UserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
		colly.Async(true),
		colly.AllowedDomains(calendarHost),
		colly.CacheDir("./academic_calendar_cache"),
	)
	_ = c.Limit(&colly.LimitRule{
		DomainGlob:  "*academiccalendars.romcmaster.ca*",
		Parallelism: 4,
		RandomDelay: 500 * time.Millisecond,
	})

	c.OnError(func(r *colly.Response, err error) {
		u := ""
		statusCode := 0
		if r != nil && r.Request != nil && r.Request.URL != nil {
			u = r.Request.URL.String()
		}
		if r != nil {
			statusCode = r.StatusCode
		}
		// The catalog contains some stale references; 404s are expected noise.
		if statusCode == 404 {
			if os.Getenv("PATHWEAVE_SCRAPER_DEBUG") != "" {
				log.Printf("scraper 404 url=%s", u)
			}
			return
		}
		log.Printf("scraper OnError url=%s err=%v", u, err)
	})

	var (
		mu      sync.Mutex
		courses []Course
	)

	c.OnHTML("td.block_content", func(e *colly.HTMLElement) {
		if !isPreviewNOPOP(e.Request.URL) {
			return
		}

		q := e.Request.URL.Query()
		catOID, coid := q.Get("catoid"), q.Get("coid")

		name := e.ChildText("#course_preview_title")
		if name == "" {
			name = strings.TrimSpace(e.ChildText("h1"))
		}

		var desc string
		e.DOM.Find("p").EachWithBreak(func(_ int, s *goquery.Selection) bool {
			if s.Find("#course_preview_title").Length() == 0 {
				return true
			}
			cl := s.Clone()
			cl.Find("#course_preview_title").Remove()
			cl.Find("h1").Remove()
			desc = squashSpaces(strings.TrimSpace(cl.Text()))
			return false
		})

		var prereqs []string
		e.DOM.Find("em a").Each(func(_ int, s *goquery.Selection) {
			if code := strings.TrimSpace(s.Text()); code != "" {
				prereqs = append(prereqs, code)
			}
		})

		var portfolioURL string
		if on, ok := e.DOM.Find("a.portfolio_link").Attr("onclick"); ok {
			if m := portfolioOnclick.FindStringSubmatch(on); len(m) == 2 {
				qstr := strings.TrimSuffix(strings.TrimSpace(m[1]), "#")
				portfolioURL = "https://" + calendarHost + "/portfolio.php?" + qstr
			}
		}

		mu.Lock()
		courses = append(courses, Course{
			PageURL:       e.Request.URL.String(),
			CatOID:        catOID,
			COID:          coid,
			PortfolioURL:  portfolioURL,
			Name:          name,
			Description:   desc,
			Prerequisites: prereqs,
		})
		mu.Unlock()
	})

	// Course list rows use showCourse(catoid, coid, ...). Restricting to this avoids
	// stale cross-reference preview links in descriptions that often 404.
	c.OnHTML(`a[onclick*="showCourse("]`, func(e *colly.HTMLElement) {
		match := showCourseArgs.FindStringSubmatch(e.Attr("onclick"))
		if len(match) < 3 {
			return
		}
		catOID, courseOID := strings.TrimSpace(match[1]), strings.TrimSpace(match[2])
		if catOID == "" || courseOID == "" {
			return
		}

		q := neturl.Values{}
		q.Set("catoid", catOID)
		q.Set("coid", courseOID)
		u := neturl.URL{
			Scheme:   "https",
			Host:     calendarHost,
			Path:     "/preview_course_nopop.php",
			RawQuery: q.Encode(),
		}
		if err := e.Request.Visit(u.String()); err != nil && !errors.Is(err, colly.ErrAlreadyVisited) {
			log.Printf("scraper Visit preview_nopop failed catoid=%s coid=%s err=%v", catOID, courseOID, err)
		}
	})

	// Course index pagination (pages 2…33, “Forward N”, etc.) — links include filter[cpage].
	c.OnHTML(`a[href*="content.php"]`, func(e *colly.HTMLElement) {
		if !isListingContentPage(e.Request.URL) {
			return
		}

		href := strings.TrimSpace(e.Attr("href"))
		if href == "" || strings.HasPrefix(strings.ToLower(href), "javascript:") {
			return
		}
		abs := strings.TrimSpace(e.Request.AbsoluteURL(href))
		if abs == "" {
			return
		}
		u, err := neturl.Parse(abs)
		if err != nil || !isListingPaginationURL(u) {
			return
		}
		if err := e.Request.Visit(abs); err != nil && !errors.Is(err, colly.ErrAlreadyVisited) {
			log.Printf("scraper listing pagination Visit failed url=%s err=%v", abs, err)
		}
	})

	// Fallback for catalogs that expand courses with hideCatalogData and href="#" only.
	c.OnHTML(`a[onclick*="hideCatalogData"]`, func(e *colly.HTMLElement) {
		match := hideCatalogArgs.FindStringSubmatch(e.Attr("onclick"))
		if len(match) < 3 {
			return
		}
		catOID, courseOID := match[1], match[2]
		q := neturl.Values{}
		q.Set("catoid", catOID)
		q.Set("coid", courseOID)

		u := neturl.URL{
			Scheme:   "https",
			Host:     calendarHost,
			Path:     "/preview_course_nopop.php",
			RawQuery: q.Encode(),
		}
		if err := e.Request.Visit(u.String()); err != nil && !errors.Is(err, colly.ErrAlreadyVisited) {
			log.Printf("scraper preview Visit failed catoid=%s coid=%s err=%v", catOID, courseOID, err)
		}
	})

	listingURL := "https://" + calendarHost + "/content.php?catoid=" + listingCatalogOID + "&navoid=" + listingNavOID
	if err := c.Visit(listingURL); err != nil {
		log.Printf("scraper listing Visit failed: %v", err)
	}
	c.Wait()

	mu.Lock()
	n := len(courses)
	mu.Unlock()
	log.Printf("scraper: collected %d course pages", n)

	if os.Getenv("PATHWEAVE_SCRAPER_DEBUG") != "" {
		for i, course := range courses {
			log.Printf("scraper[%d] name=%q url=%s", i, course.Name, course.PageURL)
		}
	}

	return courses
}
