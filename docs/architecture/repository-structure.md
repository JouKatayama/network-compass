# Repository Structure v0.1

NC-001 should create this executable skeleton without implementing later business features:

```text
network-compass/
├── AGENTS.md
├── README.md
├── CODEX_START_HERE.md
├── PROJECT_STATUS.md
├── ARCHITECTURE.md
├── docker-compose.yml
├── .env.example
├── docs/
├── apps/
│   └── web/
│       ├── AGENTS.md
│       ├── app/
│       ├── components/
│       ├── features/
│       ├── lib/
│       └── tests/
├── services/
│   └── api/
│       ├── AGENTS.md
│       ├── app/
│       │   ├── api/
│       │   ├── application/
│       │   ├── domain/
│       │   ├── infrastructure/
│       │   └── models/
│       └── tests/
├── packages/
│   └── contracts/
├── tools/
│   └── synthetic-data/
│       └── AGENTS.md
└── tests/
    └── e2e/
        └── AGENTS.md
```

NC-001 may add standard config/package files required by the stack, but it must not create fake business implementations to fill directories.
