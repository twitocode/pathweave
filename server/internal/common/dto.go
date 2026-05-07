package common

type OnboardingInfo struct {
	//Screen 1 Who are you
	Program          string   `json:"program" validate:"required"`
	Year             int      `json:"year" validate:"required,number"`
	CompletedCourses []string `json:"completed_courses" validate:"required,dive"`

	//Screen 2 Your Life
	//replace with mapbox specific stuff
	//will calculate distance myself
	WakeUpTime  string `json:"wake_up_time" validate:"required,datetime=15:04:05"`
	Bedtime     string `json:"bedtime" validate:"required,datetime=15:04:05"`
	JobInfo     string `json:"job_info" validate:"required,max=1000"`
	HomeAddress string `json:"home_address" validate:"required"`
	FuturePlans string `json:"future_plans" validate:"required,max=2000"`

	//Screen 3 Your Goals
	//1, 2, or, 3
	ProfessorQuality int      `json:"professor_quality" validate:"required,number"`
	TeachingStyle    int      `json:"teaching_style" validate:"required,number"`
	AvoidedCourses   []string `json:"avoided_courses" validate:"required,dive"`
}


type ProgramRequirementsInfo struct {
  Name string `json:"name"`
}