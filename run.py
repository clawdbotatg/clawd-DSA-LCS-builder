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
        f"\n\nFollow this pipeline:"
        f"\n1. create_repo — Delegate: set up folder + GitHub repo."
        f"\n1b. env_check — Delegate: verify ETH_PRIVATE_KEY is available (check .env file). "
        f"If missing, use leftclaw skill docs to find how to get it. "
        f"Do NOT proceed past step 2 without a working private key."
        f"\n2. scaffold — Delegate: run create-eth to scaffold SE2 with Foundry."
        f"\n3. plan — Delegate: write MASTER_PLAN.md with contract architecture, "
        f"frontend design, and deployment steps. This is the ONLY planning artifact. "
        f"Do NOT create step scripts in steps/ — they waste tokens and never get executed."
        f"\n4. build — Delegate focused sub-agent tasks: one for contracts+deploy script+tests, "
        f"one for frontend. Each sub-agent gets just the relevant section of MASTER_PLAN.md "
        f"as context via the files parameter. Do NOT paste large file contents into the task string."
        f"\n5. verify — Delegate: run forge build + forge test. If either fails, delegate a fix sub-agent. "
        f"Do NOT proceed to deployment until both pass."
        f"\n6. deploy — Delegate: deploy contract to Base, verify on Basescan, "
        f"deploy frontend to BGIPFS."
        f"\n7. complete — Call leftclaw_complete_job with the BGIPFS gateway URL."
        f"\n\nIMPORTANT:"
        f"\n- You are an ORCHESTRATOR. Use delegate() for ALL work. Do NOT call shell, "
        f"read_file, write_file, or any I/O tools directly — they are blocked for you."
        f"\n- Keep sub-agent tasks focused. Each delegate call does ONE thing."
        f"\n- Give file PATHS in delegate tasks, not file contents."
        f"\n- Tell sub-agents which files to read and which to SKIP (e.g. skip AGENTS.md, large docs)."
        f"\n- Git add + commit after each successful step (checkpoints prevent lost work)."
        f"\n- Log work on-chain after each stage."
        f"\n- Sub-agent iteration budgets: scaffold/setup tasks: 10 iters. "
        f"Contract writing: 15 iters. Frontend writing: 20 iters. "
        f"Bug fixes: 10 iters. Deployment: 10 iters. "
        f"Never set max_iterations below 10."
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
    max_cost=5.00,
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
