package gameapi

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

// TerminalObservation lives inside the bounded game session. The first result
// and its admission stay fixed even if a legacy reset reopens the board.
type TerminalObservation struct {
	Replay   bool
	first    *TerminalRound
	admitted bool
}

// TerminalResponse runs under the session lock and returns whether this
// session's original sample is included in the aggregate. A refused first
// attempt stays refused on later requests.
type TerminalResponse func(body map[string]any, round TerminalRound, first, admitted bool) bool

// WithTerminalResponse observes a terminal state in the transaction that
// produces its response, before reset or eviction can intervene.
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
			if observation == nil || observation.Replay || round.BoardID == "" ||
				round.Day == "" || round.Outcome == "" {
				return body, err
			}
			first := observation.first == nil
			if first {
				observation.first = &round
			}
			observation.admitted = respond(body, *observation.first, first, observation.admitted)
		}
		return body, err
	}
}
