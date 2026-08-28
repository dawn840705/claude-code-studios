# Unity MCP Workflow Patterns

> **컨텍스트**: Claude Code + CoplayDev/unity-mcp (HTTP localhost:8080) 통한 Unity Editor 자동화 패턴. 씬 / GameObject / 컴포넌트 / Build Settings 까지 자동.

---

## § 1 — MCP 도구 선택 기준

| 도구 | 사용 시점 |
|------|----------|
| `manage_scene` (create/load/save/get_hierarchy) | 씬 단위 작업 |
| `manage_gameobject` (create/modify/delete) | 단일 GameObject 작업 |
| `manage_components` (add/remove/set_property) | 컴포넌트 단위 작업 |
| `manage_prefabs` (modify_contents/open_prefab_stage) | prefab 편집 (Headless / Interactive 모드) |
| `find_gameobjects` | name/tag/component 검색 (instance ID 반환) |
| `execute_code` | 위 도구로 불가능한 작업 (reflection / sub-asset 매핑 / 복잡 로직) |
| `batch_execute` | **N 명령 1회 호출 — 성능 10~100x 향상** |

---

## § 2 — 핵심 패턴

### 2.1 ToolSearch 으로 schema 사전 로드

Claude Code 의 deferred tool 시스템 — schema 미로드 시 호출 실패. 작업 시작 전 `ToolSearch` 으로 일괄 로드:

```
ToolSearch select:mcp__unityMCP__manage_prefabs,mcp__unityMCP__manage_scene,mcp__unityMCP__manage_components,mcp__unityMCP__manage_gameobject,mcp__unityMCP__refresh_unity,mcp__unityMCP__execute_code,mcp__unityMCP__batch_execute,mcp__unityMCP__read_console
```

작업 중간 추가 도구 필요 시 ToolSearch 재호출.

### 2.2 batch_execute — 다수 명령 1회

10+ GameObject 생성 / 컴포넌트 set / 씬 save 등 N 명령 *1 batch* 으로 처리:

```json
{
  "commands": [
    {"tool": "manage_gameobject", "params": {"action": "create", ...}},
    {"tool": "manage_components", "params": {"action": "set_property", ...}},
    {"tool": "manage_scene", "params": {"action": "save"}}
  ]
}
```

기본 max 25 명령 / hard max 100. UI widget 일괄 생성 시 *필수* 사용 (매 명령 latency 합산 시 분 단위 지연).

### 2.3 instance ID vs path

scene GameObject 의 `target` reference:
- **instance ID** (int) — 정확. recompile / domain reload 시 변경 가능 → 작업 직후 사용.
- **path** (string) — Canvas/MainPanel/Button 형식. 비활성 GameObject 도 `find_gameobjects` + `include_inactive=true` 으로 검색.

권장:
1. `find_gameobjects` → instance ID 받기
2. batch_execute 안 같은 ID 재사용
3. recompile 후엔 다시 find

### 2.4 execute_code — reflection / sub-asset 매핑

MCP 의 standard tool 으로 불가능한 작업:
- SerializedField nested array set (예: `SlotEntry[] slotEntries`)
- InputActionReference sub-asset 매핑 (InputAction.actionMap.actions)
- Selectable.navigation Explicit set (struct)
- PrefabUtility.LoadPrefabContents 으로 prefab 직접 편집

```csharp
// 예: InputActionReference 매핑
var subAssets = UnityEditor.AssetDatabase.LoadAllAssetsAtPath("Assets/.../X.inputactions");
foreach (var sa in subAssets) {
    if (sa is InputActionReference iar && iar.name == "UI/Navigate")
        module.move = iar;
}
```

execute_code = method body 형식. `using` directive X (전체 namespace 사용).

---

## § 3 — 회귀 사고 패턴

### 3.1 set_property nested array
`manage_components.set_property` 의 nested SerializedField 배열 set 시 *outer 배열 entry* 만 생성되고 *inner ref 모두 null*. `execute_code` 으로 직접 set 권장.

### 3.2 Component 매핑 자동 reset
Button.Transition 변경 (예: Sprite Swap → Color Tint) 시 Unity 가 targetGraphic 자동 reset → *기본 첫 Image* 으로 fallback. 사장님 변경 후 *컴포넌트 ref 재검증* 필수.

### 3.3 Play mode 중 EditorSceneManager
Play 중 `EditorSceneManager.OpenScene` 호출 시 *InvalidOperationException*. 사장님께 Play 종료 안내.

### 3.4 MCP session "Session not found"
MCP server stale 또는 Unity Editor 미활성. Unity Editor focus / Claude Code `/mcp` reset.

---

## § 4 — 작업 흐름 (UI 신설 예시)

```
1. ToolSearch — 도구 schema 로드
2. read_console — 컴파일 에러 0 확인
3. manage_scene create + load — 신규 씬
4. batch_execute:
   - Main Camera + EventSystem + Canvas 생성
   - UI widget hierarchy (Panel + Buttons + Texts) 생성
   - RectTransform set + 텍스트 alignment + 컴포넌트 ref
5. find_gameobjects — instance ID 확인
6. manage_components.set_property — Manager Inspector ref 매핑
7. execute_code — nested array / Selectable.navigation Explicit set
8. manage_scene save
9. refresh_unity (compile request)
10. read_console — 에러 검증
```

---

## § 5 — 안티패턴

- ❌ 매 명령 개별 호출 (batch_execute 사용 X) — latency 폭증
- ❌ instance ID 캐싱 후 recompile 거쳐 재사용 — 깨질 수 있음
- ❌ execute_code 안에 `using` directive — codedom 컴파일 실패
- ❌ scene save 누락 — 작업 결과 손실
- ❌ `manage_scene.load` 호출 시 unsaved changes — 거부됨 (사전 save 의무)

---

## § 6 — 권장 setup

`~/.claude.json` 의 unityMCP entry:
```json
{
  "unityMCP": {
    "type": "http",
    "url": "http://localhost:8080"
  }
}
```
**`"type": "http"` 필드 필수** — 누락 시 silent fail (deferred tool 0건).
