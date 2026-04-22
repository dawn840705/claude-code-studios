# Technical Preferences

## Engine & Language

- **Engine**: Unity 6000.3.3f1 (Unity 6 LTS)
- **Language**: C# (.NET)
- **Rendering**: Universal Render Pipeline (URP) — 2D
- **Physics**: Unity 2D Physics (Box2D)

## Input & Platform

- **Target Platforms**: PC (Steam), Console (Nintendo Switch), WebGL
- **Input Methods**: Keyboard/Mouse, Gamepad
- **Primary Input**: Keyboard/Mouse (PC 우선)
- **Gamepad Support**: Full (Switch Pro Controller, Xbox, DualSense)
- **Touch Support**: None (폐기)
- **Platform Notes**: B2P 패키지. Switch 포팅 + WebGL 빌드 원활 동작이 성능 기준

## Naming Conventions

- **Classes**: PascalCase (e.g., `CastleController`, `WaveManager`)
- **Variables**: camelCase (e.g., `currentHp`, `moveSpeed`)
- **Signals/Events**: PascalCase with On prefix (e.g., `OnWaveComplete`, `OnEnemyDeath`)
- **Files**: PascalCase matching class name (e.g., `CastleController.cs`)
- **Scenes/Prefabs**: PascalCase (e.g., `MainScreen.unity`, `Goblin001.prefab`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_WAVE_COUNT`, `DEFAULT_MOVE_SPEED`)

## Performance Budgets

- **Target Framerate**: 60 FPS (Switch docked), 30 FPS minimum (Switch handheld/WebGL)
- **Frame Budget**: 16.6ms (PC/Switch docked), 33.3ms (Switch handheld/WebGL)
- **Draw Calls**: < 200 (2D, Switch GPU 기준)
- **Memory Ceiling**: 3GB (PC), 1GB (Switch), 512MB (WebGL)
- **Build Size**: < 256MB (WebGL 다운로드 최적화)
- **WebGL Notes**: SharedArrayBuffer 의존 최소화, WASM 최적화, texture compression (ETC2/ASTC)

## Testing

- **Framework**: Unity Test Framework (NUnit)
- **Minimum Coverage**: Core gameplay systems 80%+
- **Required Tests**: Balance formulas, gameplay systems, CSV data loading

## Forbidden Patterns

- Singleton 남용 (ScriptableObject 또는 DI 패턴 우선)
- Update()에서 매 프레임 GetComponent 호출
- 하드코딩된 게임플레이 수치 (CSV/ScriptableObject로 데이터 관리)
- Resources 폴더 남용 (Addressables 전환 대비)

## Allowed Libraries / Addons

- TextMeshPro (Unity 기본 포함)
- DOTween (UI 애니메이션)
- UniTask (비동기 처리)

## Architecture Decisions Log

- ADR-001: GameMaker → Unity 마이그레이션 (2D URP)
- ADR-002: CSV 데이터 → ScriptableObject 변환 파이프라인 (Resources/Data/ 기반)
- ADR-003: 플랫폼 변경 — 모바일 F2P → PC(Steam)/Console(Switch)/WebGL B2P (2026-04-16)
- ADR-004: 자원 시스템 — 골드(전투 내 통화) + 마석(메타 통화) 2종 채택 (2026-04-16)

## Engine Specialists

- **Primary**: unity-specialist
- **Language/Code Specialist**: gameplay-programmer (C#)
- **Shader Specialist**: unity-shader-specialist
- **UI Specialist**: unity-ui-specialist
- **Additional Specialists**: unity-addressables-specialist, unity-dots-specialist (필요시)
- **Routing Notes**: 2D 게임이므로 DOTS는 최적화 필요시에만 도입

### File Extension Routing

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| `.cs` (C# scripts) | gameplay-programmer |
| `.shader` / `.shadergraph` | unity-shader-specialist |
| `.uxml` / `.uss` (UI Toolkit) | unity-ui-specialist |
| `.unity` (scenes) / `.prefab` | unity-specialist |
| `.asmdef` (assembly definitions) | lead-programmer |
| General architecture review | unity-specialist |
