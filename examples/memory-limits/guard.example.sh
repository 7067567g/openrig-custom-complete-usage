#!/usr/bin/env bash
set -u

# Example only: no browser/chat killing. It only demonstrates the cgroup
# throttle path. Review thresholds before using it as a service.
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1
MEM_DSH_MB="${MEM_DSH_MB:-4000}"
MEM_DSH_HIGH="${MEM_DSH_HIGH:-5G}"
MEM_DSH_MAX="${MEM_DSH_MAX:-6G}"
MEM_DSH_SWAP_MAX="${MEM_DSH_SWAP_MAX:-1G}"

dsh_scopes() {
  systemctl --user list-units 'dsh-terminal-*.scope' --all --no-legend --plain 2>/dev/null | awk '{print $1}'
}

dsh_mem_mb() {
  local unit="$1" cur
  cur="$(systemctl --user show "$unit" --property=MemoryCurrent --value 2>/dev/null || true)"
  case "$cur" in
    ''|*[!0-9]*) echo 0 ;;
    *) echo $((cur / 1024 / 1024)) ;;
  esac
}

for unit in $(dsh_scopes); do
  mb="$(dsh_mem_mb "$unit")"
  if [ "$mb" -ge "$MEM_DSH_MB" ]; then
    echo "would throttle $unit (${mb}MB): MemoryHigh=$MEM_DSH_HIGH MemoryMax=$MEM_DSH_MAX MemorySwapMax=$MEM_DSH_SWAP_MAX"
    if [ "$DRY_RUN" -eq 0 ]; then
      systemctl --user set-property --runtime "$unit" \
        MemoryHigh="$MEM_DSH_HIGH" MemoryMax="$MEM_DSH_MAX" MemorySwapMax="$MEM_DSH_SWAP_MAX"
    fi
  fi
done
