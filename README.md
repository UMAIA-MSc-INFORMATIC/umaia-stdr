# umaia-stdr

This repository supports an MSc candidate in Informatics at UMAIA. It is structured to maintain a clear separation between documentation, source code, tests, and AI-generated artifacts.

## Repository Structure

```
umaia-stdr/
├── .ai/
│   └── AGENTS.md              # AI instructions for agents working in this repo
├── docs/
│   ├── ai-declaration/        # AI usage declaration (template + signed copy)
│   │   └── evidences/         # Evidence files supporting the AI declaration
│   ├── ai-prompts/            # All prompts used in AI sessions
│   ├── ai-logs/               # JSONL logs of all AI changes
│   ├── notes/                 # Notes and insights
│   └── references/            # Project references
├── src/                       # Source code
├── tests/                     # Test files
└── README.md                  # This file
```

## AI Instructions

For AI agents working in this repository, see [`.ai/AGENTS.md`](./.ai/AGENTS.md) for full instructions on structure, behaviors, actions, and workflows.

## Commands

The following commands are available for AI agents working in this repository:

| Command | Description |
|---------|-------------|
| `/store-prompt-session` | Stores the current prompt session as a markdown file in `docs/ai-prompts/` |
| `/initialize-repo` | Creates all mandatory folders and updates the root README.md |

See [`.ai/AGENTS.md`](./.ai/AGENTS.md) for detailed execution specifications of each command.