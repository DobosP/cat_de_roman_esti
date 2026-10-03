package httpapi

import (
	"os"
	"regexp"
	"strings"
)

// Match Django's get_host/ALLOWED_HOSTS boundary. Public anonymous requests
// remain cookie-free; a configured domain still constrains direct origin access.
var hostSyntax = regexp.MustCompile(`^([a-z0-9.-]+|\[[a-f0-9:]+\])(?::[0-9]+)?$`)

func configuredHosts() []string {
	hosts := []string{}
	for _, host := range strings.Split(os.Getenv("CAT_ALLOWED_HOSTS"), ",") {
		if host = strings.TrimFunc(host, pySpace); host != "" {
			hosts = append(hosts, strings.ToLower(host))
		}
	}
	if len(hosts) > 0 {
		return hosts
	}
	if domain := strings.TrimFunc(os.Getenv("CAT_DOMAIN"), pySpace); domain != "" {
		return []string{strings.ToLower(domain), "127.0.0.1", "localhost"}
	}
	return []string{"*"}
}
func validHost(raw string, allowed []string) bool {
	match := hostSyntax.FindStringSubmatch(strings.ToLower(raw))
	if len(match) < 2 {
		return false
	}
	domain := strings.TrimSuffix(match[1], ".")
	for _, pattern := range allowed {
		if pattern == "*" || pattern == domain || strings.HasPrefix(pattern, ".") && (domain == pattern[1:] || strings.HasSuffix(domain, pattern)) {
			return true
		}
	}
	return false
}

const badHostHTML = "\n<!doctype html>\n<html lang=\"en\">\n<head>\n  <title>Bad Request (400)</title>\n</head>\n<body>\n  <h1>Bad Request (400)</h1><p></p>\n</body>\n</html>\n"
