package common

type OnboardingInfo struct {
	//Screen 1 Who are you
	Program          string   `json:"program" validate:"required"`
	Year             int      `json:"year" validate:"required,number"`
	CompletedCourses []string `json:"completedCourses" validate:"required,dive"`

	//Screen 2 Your Life
	//replace with mapbox specific stuff
	//will calculate distance myself
	WakeUpTime  string  `json:"wakeUpTime" validate:"required,datetime=15:04"`
	Bedtime     string  `json:"bedtime" validate:"required,datetime=15:04"`
	JobInfo     string  `json:"jobInfo" validate:"max=1000"`
	Lat         float64 `json:"lat" validate:"required"`
	Lng         float64 `json:"lng" validate:"required"`
	FuturePlans string  `json:"futurePlans" validate:"max=2000"`

	//Screen 3 Your Goals
	//1, 2, or, 3
	ProfessorQuality int      `json:"professorQuality" validate:"required,number"`
	TeachingStyle    int      `json:"teachingStyle" validate:"required,number"`
	AvoidedCourses   []string `json:"avoidedCourses" validate:"required,dive"`
}

type ProgramRequirementsInfo struct {
	Name string `json:"name"`
}

type PlanInfo struct {
	Title string `json:"title"`
	Term  string `json:"term"`
}
