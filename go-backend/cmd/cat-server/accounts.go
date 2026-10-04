package main

import (
	"context"
	"errors"
	"net"
	"os"
	"strconv"
	"strings"
	"time"
	"unicode"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/accounts"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"github.com/DobosP/cat_de_roman_esti/shared-go/authcore"
	"github.com/jackc/pgx/v5/pgxpool"
)

func accountsEnabled() bool {
	switch strings.ToLower(strings.TrimFunc(os.Getenv("CAT_ACCOUNTS_ENABLED"), func(r rune) bool { return unicode.IsSpace(r) || r >= 0x1c && r <= 0x1f })) {
	case "1", "true", "yes", "on":
		return true
	}
	return false
}

func enableAccounts(ctx context.Context, handler *httpapi.Server, listen string, migrate bool) (func(), error) {
	if !accountsEnabled() {
		return func() {}, nil
	}
	dsn := os.Getenv("CAT_DATABASE_URL")
	if dsn == "" {
		dsn = os.Getenv("DATABASE_URL")
	}
	if dsn == "" {
		return nil, errors.New("CAT_ACCOUNTS_ENABLED requires CAT_DATABASE_URL")
	}
	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, errors.New("CAT_DATABASE_URL is invalid")
	}
	config.MaxConns = 4
	config.MinConns = 0
	config.MaxConnIdleTime = 5 * time.Minute
	config.MaxConnLifetime = 30 * time.Minute
	config.ConnConfig.ConnectTimeout = 5 * time.Second
	config.ConnConfig.RuntimeParams["statement_timeout"] = "5000"
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, errors.New("account database unavailable")
	}
	closeOnError := func(err error) (func(), error) { pool.Close(); return nil, err }
	if err = pool.Ping(ctx); err != nil {
		return closeOnError(errors.New("account database unavailable"))
	}
	if migrate {
		if err = accounts.Migrate(ctx, pool); err != nil {
			return closeOnError(errors.New("native account migration failed"))
		}
	}
	origin := "https://" + os.Getenv("CAT_DOMAIN")
	if os.Getenv("CAT_DOMAIN") == "" {
		if os.Getenv("CAT_DEBUG") != "1" {
			return closeOnError(errors.New("CAT_DOMAIN required for accounts outside development"))
		}
		host, port, err := net.SplitHostPort(listen)
		if err != nil {
			return closeOnError(errors.New("invalid account listen address"))
		}
		if host == "" || host == "0.0.0.0" || host == "::" {
			host = "127.0.0.1"
		}
		origin = "http://" + net.JoinHostPort(host, port)
	}
	store := accounts.NewStore(pool)
	auth, err := authcore.New(authcore.Config{PublicURL: origin, CookieName: "sessionid", GoogleClientID: os.Getenv("GOOGLE_OAUTH_CLIENT_ID"), GoogleClientSecret: os.Getenv("GOOGLE_OAUTH_CLIENT_SECRET"), FacebookClientID: os.Getenv("FACEBOOK_OAUTH_CLIENT_ID"), FacebookClientSecret: os.Getenv("FACEBOOK_OAUTH_CLIENT_SECRET"), FacebookAPIVersion: os.Getenv("FACEBOOK_API_VERSION"), OAuthCallbackPaths: map[string]string{"google": "/accounts/google/login/callback/", "facebook": "/accounts/facebook/login/callback/"}}, store)
	if err != nil {
		return closeOnError(errors.New("native account configuration invalid"))
	}
	version := os.Getenv("CAT_CONSENT_VERSION")
	if version == "" {
		version = "2026-07-09"
	}
	minAge := 16
	if value := os.Getenv("CAT_MIN_SELF_CONSENT_AGE"); value != "" {
		var parseErr error
		minAge, parseErr = strconv.Atoi(value)
		if parseErr != nil || minAge < 1 || minAge > 120 {
			return closeOnError(errors.New("CAT_MIN_SELF_CONSENT_AGE is invalid"))
		}
	}
	service := accounts.New(pool, accounts.Config{ConsentVersion: version, MinAge: minAge, DonateURL: os.Getenv("CAT_DONATE_URL"), CategoryAllowed: handler.KnownCategory}, auth)
	handler.EnableAccounts(service, auth, origin)
	return pool.Close, nil
}
