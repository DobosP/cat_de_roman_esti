package gameapi

import "fmt"

const RulesVersion = 2

type Error struct {
	Status int
	Detail any
}

func (e *Error) Error() string { return fmt.Sprint(e.Detail) }
