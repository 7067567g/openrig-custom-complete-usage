# Security

This repository is a reference implementation, not a hosted service.

## Reporting

Please use GitHub Security Advisories for private reports:

https://github.com/7067567g/SCTG-Seat-Card-Transaction-Gate-Evidence-first-orchestration-for-AI-coding-agents/security/advisories/new

Do not open a public issue for a secret leak, credential, token, or private path.
Include the file path, commit hash, and a short reproduction.

## Execution model

`g3_command` executes submission-declared commands. Treat cards and submissions
as untrusted input, run them in an isolated workspace, and do not give a
production seat self-approval authority.
