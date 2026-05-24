package main

import (
	"fmt"
	"github.com/go-playground/validator/v10"
	"testing"
)

type TestStruct struct {
	Courses []string `validate:"required,dive,required"`
}
type TestStruct2 struct {
	Courses []string `validate:"dive,required"`
}

func TestValidator(t *testing.T) {
	validate := validator.New()

	// Test 1: required on empty slice
	ts1 := TestStruct{Courses: []string{}}
	err1 := validate.Struct(ts1)
	fmt.Printf("TestStruct required empty slice err: %v\n", err1)

	// Test 2: required on nil slice
	ts2 := TestStruct{}
	err2 := validate.Struct(ts2)
	fmt.Printf("TestStruct required nil slice err: %v\n", err2)

	// Test 3: dive,required on empty slice
	ts3 := TestStruct2{Courses: []string{}}
	err3 := validate.Struct(ts3)
	fmt.Printf("TestStruct2 dive empty slice err: %v\n", err3)

	// Test 4: dive,required on nil slice
	ts4 := TestStruct2{}
	err4 := validate.Struct(ts4)
	fmt.Printf("TestStruct2 dive nil slice err: %v\n", err4)
}
