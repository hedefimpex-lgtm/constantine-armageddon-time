#!/bin/sh
set -eu

# Start Codex with the installed REA server for this session.
for program in node rea codex; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "Gerekli komut bulunamadı: $program" >&2
    exit 1
  fi
done

# Use a private runtime directory when the host mounts its Codex profile read-only.
set -- codex -c 'mcp_servers.rea.command="rea"' -c 'mcp_servers.rea.args=["mcp"]' "$@"
host_config=${CODEX_HOME:-"$HOME/.codex"}
if [ -d "$host_config" ] && [ ! -w "$host_config" ]; then
  rea_profile="${XDG_STATE_HOME:-$HOME/.local/state}/codex-rea/profile"
  (umask 077 && mkdir -p "$rea_profile")
  for entry in config.toml auth.json; do
    if [ -f "$host_config/$entry" ] && [ ! -e "$rea_profile/$entry" ]; then
      ln -s "$host_config/$entry" "$rea_profile/$entry" || [ -e "$rea_profile/$entry" ]
    fi
  done
  set -- env "CODEX_HOME=$rea_profile" "$@"
fi

exec "$@"
