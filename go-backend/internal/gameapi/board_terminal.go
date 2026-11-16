package gameapi

import "github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"

// TerminalOutcome describes the server-confirmed end of a round.
type TerminalOutcome string

const (
	TerminalWin    TerminalOutcome = "win"
	TerminalLoss   TerminalOutcome = "loss"
	TerminalGiveUp TerminalOutcome = "give_up"
)

// TerminalRound carries only board identity and outcome, without a session id,
// player identity, guesses, or a legacy account score.
type TerminalRound struct {
	BoardID string
	Day     string
	Steps   int
	Outcome TerminalOutcome
}

// TerminalObservation lives inside the bounded game session. Once captured,
// the original result stays fixed even if a legacy reset reopens the board.
type TerminalObservation struct {
	first *TerminalRound
}

func (o *TerminalObservation) observe(round TerminalRound, onFirst func(TerminalRound)) (TerminalRound, bool) {
	if o == nil || round.BoardID == "" || round.Day == "" || round.Outcome == "" {
		return TerminalRound{}, false
	}
	if o.first != nil {
		return *o.first, true
	}
	if onFirst != nil {
		o.first = &round
		onFirst(round)
	}
	return round, true
}

// TerminalResponse runs under the session lock for a terminal response. It
// receives the original result and whether this request claimed it first. It
// may add to the response but must not re-enter the session.
type TerminalResponse func(body map[string]any, round TerminalRound, first bool)

// WithTerminalResponse observes terminal state in the same transaction as an
// action or read, while the session is still pinned and its response current.
func WithTerminalResponse[T, E any](respond TerminalResponse,
	inspect func(T) (TerminalRound, *TerminalObservation), action func(T) (map[string]any, *E),
) func(T) (map[string]any, *E) {
	if respond == nil {
		return action
	}
	return func(value T) (map[string]any, *E) {
		body, err := action(value)
		if err == nil && body != nil {
			round, observation := inspect(value)
			first := false
			if result, ok := observation.observe(round, func(TerminalRound) { first = true }); ok {
				respond(body, result, first)
			}
		}
		return body, err
	}
}

// ObserveBoardTerminal reads the current terminal state through its session
// transaction. A non-nil onFirst consumes the observation and receives the
// immutable result once under that transaction. The callback must be bounded
// and must not re-enter this session. A nil callback only reads.
func ObserveBoardTerminal[T any](store *session.Store[T], id string, onFirst func(TerminalRound),
	inspect func(T) (TerminalRound, *TerminalObservation),
) (result TerminalRound, terminal bool) {
	store.Transaction(id, func(value T) error {
		round, observation := inspect(value)
		result, terminal = observation.observe(round, onFirst)
		return nil
	})
	return result, terminal
}
