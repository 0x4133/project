"""Command line interface for testing the NAN memory system with Redis storage
and Ollama integration."""

import argparse
from typing import Dict

from nan import Agent, MemoryPool, OllamaClient

agents: Dict[str, Agent] = {}
POOL = MemoryPool()
OLLAMA = OllamaClient()

def spawn_agent() -> str:
    agent_id = str(len(agents) + 1)
    agents[agent_id] = Agent(agent_id)
    return agent_id

def get_agent(agent_id: str) -> Agent:
    if agent_id not in agents:
        raise ValueError(f"Agent {agent_id} does not exist")
    return agents[agent_id]


def cmd_spawn(_args):
    agent_id = spawn_agent()
    print(f"Spawned agent {agent_id}")


def cmd_add(args):
    agent = get_agent(args.agent_id)
    agent.add_memory(args.item)
    print(f"Added memory to agent {agent.id}")


def cmd_generate(args):
    """Generate text from Ollama and store it in the agent's memory."""
    agent = get_agent(args.agent_id)
    text = OLLAMA.generate(args.prompt)
    agent.add_memory(text)
    print(text)


def cmd_query(args):
    agent = get_agent(args.agent_id)
    print("\n".join(agent.query_memory()))


def cmd_clear(args):
    agent = get_agent(args.agent_id)
    agent.clear_memory()
    print(f"Cleared memory for agent {agent.id}")


def cmd_detach(args):
    agent = get_agent(args.agent_id)
    mem_id = agent.detach_memory(POOL)
    print(f"Detached memory from agent {agent.id} -> {mem_id}")


def cmd_attach(args):
    agent = get_agent(args.agent_id)
    success = agent.attach_memory(POOL, args.memory_id)
    if success:
        print(f"Attached memory {args.memory_id} to agent {agent.id}")
    else:
        print(f"Memory ID {args.memory_id} not found")


def cmd_list_agents(_args):
    for aid in agents:
        print(aid)


def cmd_list_pool(_args):
    for mid in POOL.list_memory_ids():
        print(mid)


def build_parser():
    parser = argparse.ArgumentParser(description="NAN Memory System CLI")
    sub = parser.add_subparsers(dest="command")

    spawn = sub.add_parser("spawn", help="Spawn a new agent")
    spawn.set_defaults(func=cmd_spawn)

    add = sub.add_parser("add", help="Add memory to an agent")
    add.add_argument("agent_id")
    add.add_argument("item")
    add.set_defaults(func=cmd_add)

    query = sub.add_parser("query", help="Query agent memory")
    query.add_argument("agent_id")
    query.set_defaults(func=cmd_query)

    clear = sub.add_parser("clear", help="Clear agent memory")
    clear.add_argument("agent_id")
    clear.set_defaults(func=cmd_clear)

    gen = sub.add_parser("generate", help="Generate text with Ollama and store it")
    gen.add_argument("agent_id")
    gen.add_argument("prompt")
    gen.set_defaults(func=cmd_generate)

    detach = sub.add_parser("detach", help="Detach agent memory to pool")
    detach.add_argument("agent_id")
    detach.set_defaults(func=cmd_detach)

    attach = sub.add_parser("attach", help="Attach memory from pool to agent")
    attach.add_argument("agent_id")
    attach.add_argument("memory_id")
    attach.set_defaults(func=cmd_attach)

    la = sub.add_parser("list_agents", help="List all agents")
    la.set_defaults(func=cmd_list_agents)

    lp = sub.add_parser("list_pool", help="List memory ids in pool")
    lp.set_defaults(func=cmd_list_pool)

    return parser


def main(argv=None):
    parser = build_parser()
    if argv:
        args = parser.parse_args(argv)
        if hasattr(args, "func"):
            args.func(args)
        else:
            parser.print_help()
        return

    # Interactive mode
    while True:
        try:
            line = input("nan> ")
        except EOFError:
            break
        if line.strip().lower() in {"exit", "quit"}:
            break
        parts = line.split()
        if not parts:
            continue
        args = parser.parse_args(parts)
        if hasattr(args, "func"):
            args.func(args)


if __name__ == "__main__":
    main()

