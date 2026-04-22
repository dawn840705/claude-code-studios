# Directory Structure

```text
/
├── CLAUDE.md                        # Master configuration
├── .claude/                         # Agent definitions, skills, hooks, rules, docs
├── Assets/                          # Unity Assets root
│   ├── Scenes/                      # Unity scenes (MainScreen, Battle, etc.)
│   ├── Scripts/                     # C# game code
│   │   ├── Core/                    # Game managers, data loading, save/load
│   │   ├── Gameplay/                # Castle, cannon, civilian, monster logic
│   │   ├── AI/                      # Enemy AI, civilian AI, pathfinding
│   │   ├── UI/                      # HUD, menus, popups, inventory
│   │   └── Utils/                   # Helpers, extensions, constants
│   ├── Prefabs/                     # Reusable game objects
│   │   ├── Characters/              # Civilians, monsters, dragons
│   │   ├── Buildings/               # Castle, towers, houses
│   │   ├── Projectiles/             # Bullets, fireballs
│   │   └── UI/                      # UI prefabs
│   ├── Sprites/                     # 2D sprite assets (migrated from GameMaker)
│   ├── Resources/
│   │   └── Data/                    # CSV data tables (migrated from GameMaker)
│   ├── ScriptableObjects/           # Data-driven configs (converted from CSV)
│   ├── Animations/                  # Animator controllers + clips
│   ├── Audio/                       # SFX and music
│   └── Settings/                    # URP settings, input actions
├── Packages/                        # Unity Package Manager
├── ProjectSettings/                 # Unity project settings
├── design/                          # Game design documents
│   ├── archive/                     # Legacy GDD files (구 기획서, 참고용)
│   ├── narrative/                   # Worldbuilding, story, lore
│   └── ui/                          # UI flow, specs, wireframes
├── docs/                            # Technical documentation (architecture, postmortems)
├── production/                      # Production management (sprints, milestones)
│   ├── session-state/               # Ephemeral session state (gitignored)
│   └── session-logs/                # Session audit trail (gitignored)
└── tests/                           # Editor/PlayMode test assemblies
```
