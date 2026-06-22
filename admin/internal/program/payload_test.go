package program

import "testing"

func TestBuildPayload(t *testing.T) {
	t.Run("normalizes codes and json", func(t *testing.T) {
		payload, err := BuildPayload(FormInput{
			Name:      "Economics",
			SourceURL: " https://example.com/econ ",
			Levels: []LevelInput{{
				LevelNumber: "II",
				Index:       2,
				Groups: []GroupInput{{
					Name:      "core",
					Units:     "3-6",
					ChooseOne: true,
					Requirements: []RequirementRowInput{
						{
							CourseCode: "econ 2z03 - micro",
						},
						{
							CourseCode: "ECON 2ZZ3",
						},
						{
							CourseCode: "ECON 2Z03",
						},
					},
				}},
			}},
		})
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		if payload.Name != "Economics" {
			t.Fatalf("expected name to be trimmed, got %q", payload.Name)
		}
		if payload.SourceURL == nil || *payload.SourceURL != "https://example.com/econ" {
			t.Fatalf("expected source URL to be trimmed, got %#v", payload.SourceURL)
		}
		if got, want := len(payload.RequirementCodes), 2; got != want {
			t.Fatalf("expected %d requirement codes, got %d", want, got)
		}
		if payload.RequirementCodes[0] != "ECON 2Z03" || payload.RequirementCodes[1] != "ECON 2ZZ3" {
			t.Fatalf("unexpected codes: %#v", payload.RequirementCodes)
		}
		wantJSON := `{"levels":[{"levelNumber":"II","index":2,"groups":[{"name":"core","units":"3-6","chooseOne":true,"requirements":[{"type":"course","text":"ECON 2Z03","courseCode":"ECON 2Z03"},{"type":"course","text":"ECON 2ZZ3","courseCode":"ECON 2ZZ3"},{"type":"course","text":"ECON 2Z03","courseCode":"ECON 2Z03"}]}]}]}`
		if string(payload.RequirementsByLevel) != wantJSON {
			t.Fatalf("unexpected requirements json:\n%s", payload.RequirementsByLevel)
		}
	})

	t.Run("requires name", func(t *testing.T) {
		if _, err := BuildPayload(FormInput{}); err == nil {
			t.Fatalf("expected error for empty program name")
		}
	})

	t.Run("uses null level when no level is given", func(t *testing.T) {
		payload, err := BuildPayload(FormInput{
			Name: "Math",
			Levels: []LevelInput{{
				Index: 1,
				Groups: []GroupInput{{
					Units:        "3",
					Requirements: []RequirementRowInput{{CourseCode: "MATH 1X03"}},
				}},
			}},
		})
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		wantJSON := `{"levels":[{"levelNumber":null,"index":1,"groups":[{"units":"3","chooseOne":false,"requirements":[{"type":"course","text":"MATH 1X03","courseCode":"MATH 1X03"}]}]}]}`
		if string(payload.RequirementsByLevel) != wantJSON {
			t.Fatalf("unexpected requirements json:\n%s", payload.RequirementsByLevel)
		}
	})

	t.Run("allows text requirements without adding requirement codes", func(t *testing.T) {
		payload, err := BuildPayload(FormInput{
			Name: "Applied Psychology",
			Levels: []LevelInput{
				{
					LevelNumber: "I",
					Index:       1,
					Groups: []GroupInput{{
						Units:        "30",
						Requirements: []RequirementRowInput{{Kind: "text", Text: "(See Admission above.)"}},
					}},
				},
				{
					LevelNumber: "II",
					Index:       2,
					Groups: []GroupInput{{
						Name:         "core",
						Units:        "3",
						Requirements: []RequirementRowInput{{Kind: "course", CourseCode: "PSYCH 2AA3"}},
					}},
				},
			},
		})
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if got, want := len(payload.RequirementCodes), 1; got != want {
			t.Fatalf("expected %d requirement code, got %d", want, got)
		}
		if payload.RequirementCodes[0] != "PSYCH 2AA3" {
			t.Fatalf("unexpected codes: %#v", payload.RequirementCodes)
		}
		wantJSON := `{"levels":[{"levelNumber":"I","index":1,"groups":[{"units":"30","chooseOne":false,"requirements":[{"type":"text","text":"(See Admission above.)","courseCode":null}]}]},{"levelNumber":"II","index":2,"groups":[{"name":"core","units":"3","chooseOne":false,"requirements":[{"type":"course","text":"PSYCH 2AA3","courseCode":"PSYCH 2AA3"}]}]}]}`
		if string(payload.RequirementsByLevel) != wantJSON {
			t.Fatalf("unexpected requirements json:\n%s", payload.RequirementsByLevel)
		}
	})

	t.Run("requires at least one valid course code", func(t *testing.T) {
		_, err := BuildPayload(FormInput{
			Name: "Math",
			Levels: []LevelInput{{
				Groups: []GroupInput{{
					Requirements: []RequirementRowInput{{CourseCode: "not a course"}},
				}},
			}},
		})
		if err == nil {
			t.Fatalf("expected error for invalid course code")
		}
	})
}

func TestLevelsFromRequirements(t *testing.T) {
	levels, err := LevelsFromRequirements([]byte(`{"levels":[{"levelNumber":"II","index":2,"groups":[{"name":"core","units":"3-6","chooseOne":true,"requirements":[{"type":"course","text":"ECON 2Z03","courseCode":"ECON 2Z03"},{"type":"text","text":"Choose 3 units from List A","courseCode":null}]}]}]}`))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got, want := len(levels), 1; got != want {
		t.Fatalf("expected %d level, got %d", want, got)
	}
	if levels[0].LevelNumber != "II" || levels[0].Index != 2 || len(levels[0].Groups) != 1 {
		t.Fatalf("unexpected level: %#v", levels[0])
	}
	group := levels[0].Groups[0]
	if group.Name != "core" || group.Units != "3-6" || !group.ChooseOne || len(group.Requirements) != 2 {
		t.Fatalf("unexpected group: %#v", group)
	}
	if group.Requirements[0].Kind != "course" || group.Requirements[0].CourseCode != "ECON 2Z03" {
		t.Fatalf("unexpected course row: %#v", group.Requirements[0])
	}
	if group.Requirements[1].Kind != "text" || group.Requirements[1].Text != "Choose 3 units from List A" {
		t.Fatalf("unexpected text row: %#v", group.Requirements[1])
	}
}
