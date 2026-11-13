#!/usr/bin/env bash
set -euo pipefail

# Example only. Review limits for your host before use.
MEM_HIGH="${MEM_HIGH:-5G}"
MEM_MAX="${MEM_MAX:-6G}"
MEM_SWAP_MAX="${MEM_SWAP_MAX:-1G}"
UNIT="${UNIT:-dsh-seat-example-$(date +%s)}"

if [ "${1:-}" = "--help" ]; then
  cat <<EOF
usage: $0 [--] <command...>
  MEM_HIGH=$MEM_HIGH MEM_MAX=$MEM_MAX MEM_SWAP_MAX=$MEM_SWAP_MAX
  UNIT=$UNIT
EOF
  exit 0
fi

[ "${1:-}" = "--" ] && shift
[ "$#" -gt 0 ] || { echo "missing command" >&2; exit 2; }

exec systemd-run --user --scope --quiet \
  --unit="$UNIT" \
  --property=MemoryAccounting=yes \
  --property="MemoryHigh=$MEM_HIGH" \
  --property="MemoryMax=$MEM_MAX" \
  --property="MemorySwapMax=$MEM_SWAP_MAX" \
  -- "$@"
