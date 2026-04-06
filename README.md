# clawd-DSA-LCS-builder

An AI agent that picks up **Build jobs (Service Type 6)** from [LeftClaw Services](https://leftclaw.services) and ships decentralized apps end-to-end — Solidity contracts, Scaffold-ETH 2 frontend, deployed to Base and BGIPFS.

## What it does

1. Polls LeftClaw for open Build jobs
2. Accepts a job and spins up an orchestrator agent
3. The orchestrator delegates sub-tasks to focused sub-agents (one per contract, page, audit, fix, deployment)
4. Ships a working dapp: verified contract on Base + frontend on BGIPFS
5. Calls `leftclaw_complete_job` with the live BGIPFS URL

## Project structure

```
run.py          # Interactive CLI — run one job manually or drop into agent shell
watchJobs       # Daemon — polls LeftClaw and dispatches agents automatically
tools.py        # Agent-specific tools: deep_fetch, source_grep
system_prompt.md
builds/         # Gitignored — cloned/scaffolded repos land here
logs/           # Gitignored — per-run agent logs
```

## Setup

```bash
cp .env.example .env
# Fill in ETH_PRIVATE_KEY and any other required vars
```

Dependencies come from the shared `dead-simple-agent` library (provides the `Agent`, `make_leftclaw_tools`, `BGIPFS_TOOLS`, `JobWatcher` imports).

## Running

**Watch mode (daemon)** — polls LeftClaw every 60s, picks up jobs automatically:
```bash
python watchJobs
```

**Single job** — run the agent on a specific job ID:
```bash
python run.py --job 42
```

**Interactive shell** — drop into the agent with no job pre-loaded:
```bash
python run.py
```

## Model routing

The orchestrator uses cheap models by default and routes expensive models only where they matter:

| Model | Used for |
|---|---|
| `minimax-m2.7` | Setup, git, commands, file checks, config, diagnostics |
| `claude-sonnet-4.6` | Planning, fixing compile/test errors, deployment |
| `claude-opus-4.6` | Writing smart contracts, tests, frontend page.tsx |

## Build pipeline

Each job follows this pipeline, logged on-chain after each stage:

```
create_repo → scaffold → plan (MASTER_PLAN.md) → build → verify → deploy → complete
```

The orchestrator is **tools-blocked** from direct I/O — it can only use `delegate()`. All real work happens in sub-agents with scoped iteration budgets and skill routing.

## Skills

Skill docs are fetched at startup:
- `leftclaw.services/admin/skill.md` — LeftClaw platform
- `ethskills.com/SKILL.md` — Solidity, Foundry, deployment patterns
- `docs.scaffoldeth.io/SKILL.md` — Scaffold-ETH 2
- `bgipfs.com/SKILL.md` — IPFS deployment

## Security

- `ETH_PRIVATE_KEY` is read from `.env` and used automatically by tools — never logged or exposed
- Client wallet (`job.client`) is set as owner on all deployed contracts
- `.env` is gitignored
