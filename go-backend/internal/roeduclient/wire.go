package roeduclient

import (
	"errors"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

// Refuse ambiguous bindings and invalid Unicode before decoding external pages.
func validateWire(raw []byte) error {
	if strictjson.Validate(raw) != nil {
		return errors.New("RO-EDU invalid, ambiguous or non-scalar Unicode JSON response")
	}
	return nil
}
