#!/usr/bin/env python3
from agent import Agent
from agent.leftclaw import make_leftclaw_tools
from agent.bgipfs import BGIPFS_TOOLS
from tools import TOOLS

import os
import sys

job_prompt = None
if "--job" in sys.argv:
    idx = sys.argv.index("--job")
    job_id = sys.argv[idx + 1]
    del sys.argv[idx:idx + 2]
    os.environ.setdefault("LLM_PROXY_JOB_NAME", f"job-{job_id}")
    job_prompt = (
        f"You have a Build job to complete. Job #{job_id} on LeftClaw Services. "
        f"Use leftclaw_get_job to read the full description, "
        f"leftclaw_get_messages to check for client messages. "
        f"Note the job.client address — this is who owns everything you build."
        f"\n\nSTART FRESH — create ./builds/leftclaw-service-job-{job_id}_$(date +%s) "
        f"as your build folder. Do NOT look at or reuse any existing folders. "
        f"Create the folder and GitHub repo in your FIRST action."

        f"\n\n=== PIPELINE ==="
        f"\n1. create_repo — Delegate: set up folder + GitHub repo."
        f"\n1b. env_check — Delegate: verify ETH_PRIVATE_KEY is available (check .env file). "
        f"If missing, use leftclaw skill docs to find how to get it. "
        f"Do NOT proceed past step 2 without a working private key."
        f"\n2. scaffold — Delegate: run create-eth to scaffold SE2 with Foundry."
        f"\n3. plan — Delegate: write MASTER_PLAN.md (architecture, contracts, frontend, deploy). "
        f"This is the ONLY planning artifact. No step scripts."
        f"\n4. build — Delegate: one sub-agent for contracts+deploy script+tests, "
        f"one for frontend page.tsx."
        f"\n5. verify — Delegate: run forge build + forge test. Fix failures before proceeding."
        f"\n6. deploy — Delegate: deploy contract to Base, verify, deploy frontend to BGIPFS."
        f"\n7. complete — Call leftclaw_complete_job with the BGIPFS gateway URL."

        f"\n\n=== MODEL ROUTING ==="
        f"\nChoose the model for each delegate() call:"
        f"\n  minimax-m2.7 (default): setup, git, running commands, checking files, config patches, diagnostics"
        f"\n  claude-sonnet-4.6: writing MASTER_PLAN.md, fixing compile/test errors, deployment tasks"
        f"\n  claude-opus-4.6: writing smart contracts, writing tests, writing frontend page.tsx"
        f"\n  Rule: any task that produces important code MUST use opus."
        f"\n  When using sonnet/opus: ALWAYS set skip_default_skills=true and only pass the needed skill(s)."
        f"\n  Keep task descriptions SHORT for expensive models. Give file paths, not content."

        f"\n\n=== SKILL ROUTING ==="
        f"\nSet skills and skip_default_skills=true on EVERY delegate call:"
        f"\n  Writing Solidity / forge / contract bugs → skills: [\"ethskills\"]"
        f"\n  Scaffolding with create-eth             → skills: [\"scaffoldeth\"]"
        f"\n  Building frontend / SE2 hooks            → skills: [\"scaffoldeth\"]"
        f"\n  Writing MASTER_PLAN.md                   → skills: [\"ethskills\", \"scaffoldeth\"]"
        f"\n  Deploying to IPFS                        → skills: [\"bgipfs\"]"
        f"\n  Deploying contracts to chain              → skills: [\"ethskills\"]"
        f"\n  Shell commands, file checks, git          → skills: [] (no skills needed)"
        f"\n  leftclaw is orchestrator-only — never pass it to sub-agents."

        f"\n\n=== FILE PRELOADING ==="
        f"\nUse the files parameter to preload what sub-agents need (saves iterations):"
        f"\n  Contract writing → files: [MASTER_PLAN.md, foundry.toml]"
        f"\n  Frontend writing → files: [MASTER_PLAN.md, scaffold.config.ts, existing page.tsx]"
        f"\n  Test fixing      → files: [failing test file, contract file]"
        f"\n  Deploy           → files: [.env, foundry.toml, MASTER_PLAN.md]"

        f"\n\n=== RETRY RULES ==="
        f"\nIf a delegate fails or hits max_iterations:"
        f"\n- Do NOT re-delegate the same task with different wording."
        f"\n- After 1 failure: break the task into smaller, more specific sub-tasks."
        f"\n- After 2 failures on the same goal: delegate a diagnostic task first "
        f"(\"list the directory\", \"read the error\") to understand WHY before trying again."
        f"\n- Never delegate the same task more than 3 times total."

        f"\n\n=== RULES ==="
        f"\n- You are an ORCHESTRATOR. Use delegate() for ALL work. "
        f"Shell, read_file, write_file are BLOCKED for you."
        f"\n- Log work on-chain only at major stages: create_repo, scaffold, build, verify, deploy, complete. "
        f"Do NOT log after every sub-step."
        f"\n- Git add + commit after each successful step."
        f"\n- Sub-agent iteration budgets: setup: 10. Contracts: 15. Frontend: 20. "
        f"Fixes: 10. Deploy: 10. Never below 10."
    )

model = os.environ.get("AGENT_MODEL", "minimax-m2.7")
sys.argv[1:1] = [model, "--provider", "bankr"]

LEFTCLAW = make_leftclaw_tools(service_type_id=6)

SKILLS = [
    "https://leftclaw.services/admin/skill.md",
    "https://ethskills.com/SKILL.md",
    "https://docs.scaffoldeth.io/SKILL.md",
    "https://www.bgipfs.com/SKILL.md",
]

if job_prompt:
    sys.argv.append(job_prompt)

Agent(
    extra_tools=LEFTCLAW + BGIPFS_TOOLS + TOOLS,
    max_cost=10.00,
    preload_skills=SKILLS,
    default_skills=["leftclaw", "ethskills", "scaffoldeth"],
    exclude_tools=[
        "shell", "read_file", "write_file", "patch_file",
        "fetch_url", "deep_fetch", "source_grep",
        "github_list_repos", "github_read_file", "github_write_file",
        "github_list_issues", "github_create_issue", "github_search_code",
        "github_create_pr",
        "bgipfs_upload",
    ],
).cli()
