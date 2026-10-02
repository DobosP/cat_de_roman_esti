package gameapi

import "fmt"

type Error struct {
	Status int
	Detail any
}

func (e *Error) Error() string { return fmt.Sprint(e.Detail) }
