module github.com/DobosP/cat_de_roman_esti/go-backend

go 1.27.1

require (
	github.com/a-h/templ v0.3.1070 // indirect
	github.com/coreos/go-oidc/v3 v3.21.0 // indirect
	github.com/flosch/pongo2/v6 v6.1.0 // indirect
	github.com/go-jose/go-jose/v4 v4.1.4 // indirect
	github.com/jackc/pgpassfile v1.0.0 // indirect
	github.com/jackc/pgservicefile v0.0.0-20240606120523-5a60cdf6a761 // indirect
	github.com/jackc/puddle/v2 v2.2.2 // indirect
	github.com/rogpeppe/go-internal v1.16.0 // indirect
	github.com/vearutop/statigz v1.5.0 // indirect
	golang.org/x/crypto v0.57.0 // indirect
	golang.org/x/oauth2 v0.37.0 // indirect
	golang.org/x/sync v0.23.0 // indirect
	golang.org/x/sys v0.48.0 // indirect
	golang.org/x/text v0.42.0 // indirect
)

replace github.com/DobosP/cat_de_roman_esti/shared-go/authcore => ../shared-go/authcore

require (
	github.com/DobosP/cat_de_roman_esti/shared-go/authcore v0.0.0
	github.com/DobosP/roedu-ui/web-kit v0.0.0-core-v1.6
	github.com/andybalholm/brotli v1.2.6
	github.com/jackc/pgx/v5 v5.11.0
	golang.org/x/net v0.59.0
)

replace github.com/DobosP/roedu-ui/web-kit => ./third_party/webkit
