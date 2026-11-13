#!/usr/bin/env python3
# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
import json, sys
from pathlib import Path

def check(sub_path: Path, schema_path: Path):
    sub=json.loads(sub_path.read_text(encoding='utf-8'))
    schema=json.loads(schema_path.read_text(encoding='utf-8'))
    try:
        import jsonschema
        jsonschema.validate(sub, schema)
        return {"verdict":"PASS","reason":"schema validated"}
    except Exception as e:
        # Fallback: minimal required/type check
        missing=[k for k in schema.get('required',[]) if k not in sub]
        if missing:
            return {"verdict":"FAIL","reason":f"missing fields: {missing}"}
        if sub.get('status') not in ('OK','BLOCKED'):
            return {"verdict":"FAIL","reason":"status must be OK or BLOCKED"}
        return {"verdict":"FAIL","reason":f"schema validation failed: {e}"}

if __name__ == '__main__':
    r=check(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r['verdict']=='PASS' else 1)
