package program

import (
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
)

var courseCodePattern = regexp.MustCompile(`\b([A-Z]{2,10}\s\d[A-Z0-9]{2,4})\b`)

type FormInput struct {
	Name      string       `json:"name"`
	SourceURL string       `json:"sourceUrl"`
	Levels    []LevelInput `json:"levels"`
}

type RequirementRowInput struct {
	Kind       string `json:"kind"`
	CourseCode string `json:"courseCode"`
	Text       string `json:"text"`
}

type LevelInput struct {
	LevelNumber string       `json:"levelNumber"`
	Index       int          `json:"index"`
	Groups      []GroupInput `json:"groups"`
}

type GroupInput struct {
	Name         string                `json:"name"`
	Units        string                `json:"units"`
	ChooseOne    bool                  `json:"chooseOne"`
	Requirements []RequirementRowInput `json:"requirements"`
}

type UpsertPayload struct {
	Name                string
	SourceURL           *string
	RequirementCodes    []string
	RequirementsByLevel json.RawMessage
	Levels              []LevelInput
}

type Summary struct {
	ID   int64
	Name string
}

type EditableProgram struct {
	ID        int64
	Name      string
	SourceURL string
	Levels    []LevelInput
}

func BuildPayload(input FormInput) (UpsertPayload, error) {
	name := strings.TrimSpace(input.Name)
	if name == "" {
		return UpsertPayload{}, fmt.Errorf("program name is required")
	}

	codes, requirementsByLevel, err := buildRequirements(input.Levels)
	if err != nil {
		return UpsertPayload{}, err
	}

	var sourceURL *string
	if trimmedURL := strings.TrimSpace(input.SourceURL); trimmedURL != "" {
		sourceURL = &trimmedURL
	}

	return UpsertPayload{
		Name:                name,
		SourceURL:           sourceURL,
		RequirementCodes:    codes,
		RequirementsByLevel: requirementsByLevel,
		Levels:              input.Levels,
	}, nil
}

func buildRequirements(inputLevels []LevelInput) ([]string, json.RawMessage, error) {
	codes := make([]string, 0)
	seenCodes := make(map[string]struct{})
	levels := make([]requirementLevel, 0, len(inputLevels))

	for levelIdx, inputLevel := range inputLevels {
		level := requirementLevel{
			LevelNumber: nullableString(strings.TrimSpace(inputLevel.LevelNumber)),
			Index:       normalizedIndex(inputLevel.Index, levelIdx),
			Groups:      []unitGroup{},
		}

		for _, inputGroup := range inputLevel.Groups {
			group := unitGroup{
				Name:         strings.TrimSpace(inputGroup.Name),
				Units:        strings.TrimSpace(inputGroup.Units),
				ChooseOne:    inputGroup.ChooseOne,
				Requirements: []requirementItem{},
			}

			for _, inputRequirement := range inputGroup.Requirements {
				item, code, ok := buildRequirementItem(inputRequirement)
				if !ok {
					continue
				}
				if code != "" {
					if _, exists := seenCodes[code]; !exists {
						seenCodes[code] = struct{}{}
						codes = append(codes, code)
					}
				}
				group.Requirements = append(group.Requirements, item)
			}

			if len(group.Requirements) > 0 {
				level.Groups = append(level.Groups, group)
			}
		}

		if len(level.Groups) > 0 {
			levels = append(levels, level)
		}
	}

	if len(levels) == 0 {
		return nil, nil, fmt.Errorf("at least one course or text requirement is required")
	}

	requirementsByLevel, err := json.Marshal(requirementDocument{Levels: levels})
	if err != nil {
		return nil, nil, fmt.Errorf("requirements JSON normalization failed: %w", err)
	}
	return codes, requirementsByLevel, nil
}

type requirementLevel struct {
	LevelNumber *string     `json:"levelNumber"`
	Index       int         `json:"index"`
	Groups      []unitGroup `json:"groups"`
}

type unitGroup struct {
	Name         string            `json:"name,omitempty"`
	Group        string            `json:"group,omitempty"`
	Units        string            `json:"units"`
	ChooseOne    bool              `json:"chooseOne"`
	Requirements []requirementItem `json:"requirements"`
}

type requirementDocument struct {
	Levels []requirementLevel `json:"levels"`
}

type requirementItem struct {
	Type       string  `json:"type"`
	Text       string  `json:"text"`
	CourseCode *string `json:"courseCode"`
}

func buildRequirementItem(row RequirementRowInput) (requirementItem, string, bool) {
	kind := strings.ToLower(strings.TrimSpace(row.Kind))
	if kind == "" {
		kind = "course"
	}

	if kind == "text" {
		text := strings.TrimSpace(row.Text)
		if text == "" {
			return requirementItem{}, "", false
		}
		return requirementItem{
			Type:       "text",
			Text:       text,
			CourseCode: nil,
		}, "", true
	}

	matches := courseCodePattern.FindStringSubmatch(strings.ToUpper(strings.TrimSpace(row.CourseCode)))
	if len(matches) < 2 {
		return requirementItem{}, "", false
	}
	code := strings.TrimSpace(matches[1])
	return requirementItem{
		Type:       "course",
		Text:       code,
		CourseCode: &code,
	}, code, true
}

func nullableString(value string) *string {
	if value == "" {
		return nil
	}
	return &value
}

func normalizedIndex(value int, fallback int) int {
	if value > 0 {
		return value
	}
	return fallback + 1
}

func LevelsFromRequirements(requirementsByLevel []byte) ([]LevelInput, error) {
	if len(requirementsByLevel) == 0 {
		return nil, nil
	}

	var doc requirementDocument
	if err := json.Unmarshal(requirementsByLevel, &doc); err == nil && doc.Levels != nil {
		return editableLevelsFromDocument(doc), nil
	}

	var legacyLevels []legacyRequirementLevel
	if err := json.Unmarshal(requirementsByLevel, &legacyLevels); err != nil {
		return nil, fmt.Errorf("parse requirements by level: %w", err)
	}
	return editableLevelsFromLegacy(legacyLevels), nil
}

func editableLevelsFromDocument(doc requirementDocument) []LevelInput {
	levels := make([]LevelInput, 0, len(doc.Levels))
	for _, level := range doc.Levels {
		input := LevelInput{Index: level.Index}
		if level.LevelNumber != nil {
			input.LevelNumber = *level.LevelNumber
		}
		for _, group := range level.Groups {
			input.Groups = append(input.Groups, groupInputFromUnitGroup(group))
		}
		levels = append(levels, input)
	}
	return levels
}

type legacyRequirementLevel struct {
	Level      *string     `json:"level"`
	UnitGroups []unitGroup `json:"unitGroups"`
}

func editableLevelsFromLegacy(legacyLevels []legacyRequirementLevel) []LevelInput {
	levels := make([]LevelInput, 0, len(legacyLevels))
	for i, level := range legacyLevels {
		input := LevelInput{Index: i + 1}
		if level.Level != nil {
			input.LevelNumber = *level.Level
		}
		for _, group := range level.UnitGroups {
			input.Groups = append(input.Groups, groupInputFromUnitGroup(group))
		}
		levels = append(levels, input)
	}
	return levels
}

func groupInputFromUnitGroup(group unitGroup) GroupInput {
	name := group.Name
	if name == "" {
		name = group.Group
	}
	input := GroupInput{
		Name:      name,
		Units:     group.Units,
		ChooseOne: group.ChooseOne,
	}
	for _, requirement := range group.Requirements {
		row := RequirementRowInput{
			Kind: requirement.Type,
			Text: requirement.Text,
		}
		if row.Kind == "" {
			row.Kind = "course"
		}
		if requirement.CourseCode != nil {
			row.CourseCode = *requirement.CourseCode
		}
		input.Requirements = append(input.Requirements, row)
	}
	return input
}
