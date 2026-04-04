#!/usr/bin/env python3
from agent import Agent
from agent.leftclaw import make_leftclaw_tools
from agent.bgipfs import BGIPFS_TOOLS
from tools import TOOLS

import os
import sys

model = os.environ.get("AGENT_MODEL", "claude-opus-4.6")
sys.argv[1:1] = [model, "--provider", "bankr"]

LEFTCLAW = make_leftclaw_tools(service_type_id=6)
Agent(extra_tools=LEFTCLAW + BGIPFS_TOOLS + TOOLS, max_iterations=40).cli()
