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
        f"\n1. create_repo — Delegate: set up folder + GitHub repo. "
        f"Pass tools: ['github_create_repo', 'github_write_file']."
        f"\n1b. env_check — Delegate: verify ETH_PRIVATE_KEY is available (check .env file). "
        f"If missing, use leftclaw skill docs to find how to get it. "
        f"Do NOT proceed past step 2 without a working private key."
        f"\n2. scaffold — Delegate: scaffold SE2 with Foundry. "
        f"EXACT command: `cd ./builds/leftclaw-service-job-{job_id} && npx -y create-eth@latest . -s foundry`. "
        f"The -s flag selects the Solidity framework. No other flags exist (no --template, --chain, --skip-git). "
        f"Directory MUST be empty — move any existing files out first, scaffold, then move them back."
        f"\n   SE2 v2 PROJECT STRUCTURE (after scaffold):"
        f"\n     packages/foundry/contracts/   — Solidity contracts"
        f"\n     packages/foundry/script/      — Forge deploy scripts"
        f"\n     packages/foundry/test/        — Forge tests"
        f"\n     packages/nextjs/app/page.tsx  — Frontend page (Next.js App Router)"
        f"\n     packages/nextjs/scaffold.config.ts — Chain config"
        f"\n   ⚠️ There is NO packages/react-app/. That was SE2 v1. Do NOT use that path."
        f"\n3. plan — Delegate: write MASTER_PLAN.md (architecture, contracts, frontend, deploy). "
        f"This is the ONLY planning artifact. No step scripts. "
        f"Tell sonnet to use EXACT file paths from the structure above."
        f"\n4. build — Delegate one opus sub-agent for contracts+deploy script+tests, "
        f"one opus sub-agent for frontend page.tsx. "
        f"\n   FILE PRELOADING IS CRITICAL — opus sub-agents will waste all iterations exploring if files are missing."
        f"\n   Contracts delegate files: [MASTER_PLAN.md, foundry.toml, DeployHelpers.s.sol, DeployYourContract.s.sol, YourContract.sol, YourContract.t.sol]"
        f"\n   Frontend delegate files: [AGENTS.md, scaffold.config.ts, page.tsx, "
        f"the smart contract .sol file you just wrote]. "
        f"Do NOT preload MASTER_PLAN.md for frontend — the contract .sol has the function signatures, "
        f"and AGENTS.md has the hook API. That's all opus needs."
        f"\n   The task description should specify: what the page does, the contract name, "
        f"and the output file path. Keep it SHORT — opus is expensive."
        f"\n   AGENTS.md is MANDATORY — it has hook API (useScaffoldReadContract, useScaffoldWriteContract)."
        f"\n   The contract .sol is MANDATORY — opus needs the function signatures."
        f"\n4b. validate — Delegate (minimax): verify that build sub-agents actually wrote files. "
        f"Run: `wc -l` and `head -5` on each expected output file "
        f"(the contract .sol, deploy script .s.sol, test .t.sol, and page.tsx). "
        f"If ANY file is missing, empty, or still contains the scaffold template, "
        f"do NOT proceed — re-delegate the failed build task with a different approach."
        f"\n5. verify — Delegate: run forge build + forge test. Fix failures before proceeding."
        f"\n6. deploy — Two separate sonnet delegates:"
        f"\n   a) Deploy contract to Base MAINNET (chain id 8453, rpc https://mainnet.base.org). "
        f"Use the ETH_PRIVATE_KEY from the ROOT ./.env file (NOT the build folder .env). "
        f"Preload files: [./.env, foundry.toml, deploy script]."
        f"\n   b) Build + upload frontend to BGIPFS. "
        f"Pass tools: ['bgipfs_upload'] — this is the ONLY way to upload to IPFS. "
        f"Preload files: [scaffold.config.ts, deployedContracts.ts]."
        f"\n7. complete — Call leftclaw_complete_job with the BGIPFS gateway URL."

        f"\n\n=== MODEL ROUTING ==="
        f"\nChoose the model for each delegate() call:"
        f"\n  minimax-m2.7 (default): setup, git, running commands, checking files, config patches, diagnostics"
        f"\n  claude-sonnet-4.6: writing MASTER_PLAN.md, fixing compile/test errors, deployment tasks"
        f"\n  claude-opus-4.6: writing smart contracts, writing tests, writing frontend page.tsx"
        f"\n  Rule: any task that produces important code MUST use opus."
        f"\n  Rule: checking/verifying files (ls, read, forge build/test) should use minimax, not opus or sonnet."
        f"\n  When using sonnet/opus: ALWAYS set skip_default_skills=true and only pass the needed skill(s)."
        f"\n  Keep task descriptions SHORT for expensive models. Give file paths, not content."

        f"\n\n=== SKILL ROUTING ==="
        f"\nSet skills and skip_default_skills=true on EVERY delegate call:"
        f"\n  Writing Solidity / forge / contract bugs → skills: [\"ethskills\"]"
        f"\n  Scaffolding with create-eth             → skills: [\"scaffoldeth\"]"
        f"\n  Building frontend / SE2 hooks            → skills: [] (NO skill — preload AGENTS.md as a file instead)"
        f"\n  Writing MASTER_PLAN.md                   → skills: [\"ethskills\", \"scaffoldeth\"]"
        f"\n  Deploying to IPFS                        → skills: [\"bgipfs\"]"
        f"\n  Deploying contracts to chain              → skills: [\"ethskills\"]"
        f"\n  Shell commands, file checks, git          → skills: [] (no skills needed)"
        f"\n  leftclaw is orchestrator-only — never pass it to sub-agents."
        f"\n  ⚠️ NEVER pass scaffoldeth skill to opus/sonnet frontend-writing sub-agents. "
        f"It tells them to run Steps 1-3 (scaffold, read AGENTS.md, read skill files) which wastes all iterations. "
        f"Instead, preload AGENTS.md as a file — it has the hook API they need."

        f"\n\n=== FILE PRELOADING ==="
        f"\nUse the files parameter to preload what sub-agents need (saves iterations):"
        f"\n  Contract writing → files: [MASTER_PLAN.md, foundry.toml, YourContract.sol, DeployYourContract.s.sol, DeployHelpers.s.sol]"
        f"\n  Frontend writing → files: [AGENTS.md, scaffold.config.ts, page.tsx, the contract .sol file]"
        f"\n  (No MASTER_PLAN.md for frontend — the .sol file has function sigs, AGENTS.md has hook API. Keeps context small.)"
        f"\n  Test fixing      → files: [failing test file, contract file]"
        f"\n  Deploy           → files: [.env, foundry.toml, MASTER_PLAN.md]"

        f"\n\n=== RETRY RULES ==="
        f"\nIf a delegate fails or hits max_iterations:"
        f"\n- Do NOT re-delegate the same task with different wording."
        f"\n- After 1 failure: break the task into smaller, more specific sub-tasks."
        f"\n- After 2 failures on the same goal: delegate a diagnostic task first "
        f"(\"list the directory\", \"read the error\") to understand WHY before trying again."
        f"\n- Never delegate the same task more than 3 times total."
        f"\n- If an opus sub-agent hits max_iterations without writing files, "
        f"include the EXACT file content in the task description and tell it to write_file immediately. "
        f"Or switch to sonnet/minimax with a shell heredoc approach."

        f"\n\n=== RULES ==="
        f"\n- You are an ORCHESTRATOR. Use delegate() for ALL work. "
        f"Shell, read_file, write_file are BLOCKED for you."
        f"\n- Log work on-chain only at major stages: create_repo, scaffold, build, verify, deploy, complete. "
        f"Do NOT log after every sub-step."
        f"\n- Git add + commit after each successful step."
        f"\n- Sub-agent iteration budgets: setup: 10. Contracts (opus): 8. Frontend (opus): 8. "
        f"Fixes: 10. Deploy: 10. Never below 5."
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
    max_cost=3.00,
    preload_skills=SKILLS,
    default_skills=["leftclaw", "ethskills", "scaffoldeth"],
    exclude_tools=[
        "shell", "read_file", "write_file", "patch_file",
        "fetch_url", "deep_fetch", "source_grep",
        "github_list_repos", "github_read_file", "github_write_file",
        "github_create_repo",
        "github_list_issues", "github_create_issue", "github_search_code",
        "github_create_pr",
        "bgipfs_upload",
    ],
).cli()
