"""Tool definitions + dispatcher for Nia."""
import web
import journal as _journal

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Store a durable fact about this person's situation — their case, their rights, their history with a creditor, custody battle, housing situation. Anything important they've told you that you should never forget.",
            "parameters": {
                "type": "object",
                "properties": {"fact": {"type": "string"}},
                "required": ["fact"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_goal",
            "description": "Track a goal, action item, or next step for Brian — something he needs to do or wants to accomplish.",
            "parameters": {
                "type": "object",
                "properties": {"goal": {"type": "string"}},
                "required": ["goal"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_goal",
            "description": "Mark a goal as completed when Brian reports finishing it.",
            "parameters": {
                "type": "object",
                "properties": {"goal": {"type": "string", "description": "Fragment of the goal text to match"}},
                "required": ["goal"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for current laws, bills, court rulings, local resources, news, grants, or any information needed to give the person a real answer with receipts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_article",
            "description": "Read the full text of a web page — a law, a court ruling, a news article, a resource directory. Use after web_search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to read"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "journal_entry",
            "description": "Save a journal entry for Brian — a reflection, goal, lesson, or thought he wants to preserve.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The journal entry content"},
                    "prompt": {"type": "string", "description": "Optional: the journaling question or category"},
                },
                "required": ["text"],
            },
        },
    },
]


def dispatch(name, args, memory=None):
    if name == "remember_fact":
        fact = args.get("fact", "").strip()
        if fact and memory is not None:
            memory.remember(fact)
            print(f"  [memory] stored: {fact}")
        return "stored"

    if name == "add_goal":
        goal = args.get("goal", "").strip()
        if goal and memory is not None:
            gid = memory.add_goal(goal)
            print(f"  [memory] goal added [{gid}]: {goal}")
            return f"goal added: {goal}"
        return "no goal text given"

    if name == "complete_goal":
        frag = args.get("goal", "").strip()
        if frag and memory is not None:
            matched = memory.complete_goal(frag)
            if matched:
                print(f"  [memory] goal completed: {matched}")
                return f"completed: {matched}"
            return "no matching active goal found"
        return "no goal text given"

    if name == "web_search":
        query = args.get("query", "").strip()
        if not query:
            return "no query given"
        print(f"  [web] searching: {query}")
        try:
            results = web.search(query)
            return "\n".join(
                f"- {r['title']}: {r['snippet']} ({r['url']})"
                for r in results
            ) or "no results"
        except Exception as e:
            return f"search failed: {e}"

    if name == "read_article":
        url = args.get("url", "").strip()
        if not url:
            return "no url given"
        print(f"  [web] reading: {url}")
        try:
            return web.read_url(url)
        except Exception as e:
            return f"could not read page: {e}"

    if name == "journal_entry":
        text = args.get("text", "").strip()
        prompt = args.get("prompt", "")
        if not text:
            return "no entry text given"
        result = _journal.save_entry(text, prompt=prompt)
        print(f"  [journal] {result}")
        return result

    print(f"  [tools] unknown tool: {name}")
    return None
