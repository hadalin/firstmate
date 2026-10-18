#!/usr/bin/env bash
set -euo pipefail
REPO=$PWD
LAB=$PWD/.test-tmp/report-lab
trap 'rm -rf "$LAB"' EXIT
bin/fm-lab-home.sh create "$LAB" >/dev/null
export FM_HOME=$LAB FM_STATE_OVERRIDE=$LAB/state FM_CONFIG_OVERRIDE=$LAB/config FM_DATA_OVERRIDE=$LAB/data
export FM_SUPERVISION_ACTOR=branch FM_BRANCH_REPORT_TURN=live.1
run_case() {
  local name=$1 posture=$2 finished=$3 silent=$4 expected=$5
  rm -f "$LAB/state/branch-outcomes.jsonl" "$LAB/state/.branch-outcomes-cursor" "$LAB/state/.branch-outcomes-processed"
  printf 'turn=live.1\nrows=1\ntasks=scout-a scout-ab\nunscoped=0\nwake=signal: scout-a.status done: report ready\nposture=%s\nfinished_scouts=%s\n' "$posture" "$finished" > "$LAB/state/.supervision-host-turn"
  printf '\nCASE: %s\n' "$name"
  "$REPO/bin/fm-branch-report.sh" --task scout-a --verdict routine --silent "$silent" --summary "$name"
  cat "$LAB/state/branch-outcomes.jsonl"
  python3 - "$LAB/state/branch-outcomes.jsonl" "$expected" "$silent" <<'PY'
import json,sys
r=json.loads(open(sys.argv[1]).read())
assert r['verdict']==sys.argv[2],r
assert r['silent']==(False if sys.argv[2]=='captain' else sys.argv[3]=='true'),r
PY
}
run_case 'Finished scout after metadata cleanup' attended scout-a false captain
run_case 'Silent routine cannot suppress a finished scout' attended scout-a true captain
run_case 'Task prefix is not a finished scout match' attended scout-ab false routine
run_case 'Unfinished task stays routine' attended '' false routine
run_case 'Turn begun away stays routine after return' away scout-a true routine
"$REPO/bin/fm-afk-contract.sh" enter --words 'Disposable test away posture' >/dev/null
run_case 'Captain leaves during attended turn' attended scout-a true routine
"$REPO/bin/fm-afk-contract.sh" archive >/dev/null
printf '\nCASE: Out-of-scope report is refused\n'
set +e
"$REPO/bin/fm-branch-report.sh" --task other --verdict routine --summary 'must refuse'
rc=$?
set -e
[ "$rc" = 3 ]
printf 'exit=%s; store rows=%s\n' "$rc" "$(wc -l < "$LAB/state/branch-outcomes.jsonl")"

run_case 'Finished report is presented to MAIN after cleanup' attended scout-a false captain
: > "$LAB/config/supervision-host"
printf '\nMAIN drain:\n'
FM_SUPERVISION_ACTOR=main "$REPO/bin/fm-wake-drain.sh" || true
