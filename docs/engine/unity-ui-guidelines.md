# Unity UI/UX Guidelines (uGUI + Input System 1.x)

> **컨텍스트**: Unity uGUI (Canvas/Button/Image/TMP_Text) + `com.unity.inputsystem` 1.x 기반 게임 UI 의 영구 룰. PC + Gamepad 2스킴 (또는 +터치) 동시 대응 게임용.
>
> 본 문서는 **5 영구 룰** 의 통합 spec. 신규 UI 작성 시 *반드시* 적용.

---

## § 1 — 영구 룰 cluster (5건)

### Rule 1: UI 활성 시 첫 selectable 자동 select

**Why**: 게임패드 navigation 은 `EventSystem.currentSelectedGameObject` 가 있어야 작동. UI 활성 직후 `EventSystem.SetSelectedGameObject` 직접 호출 = 1프레임 늦은 EventSystem refresh 로 무시됨.

**Pattern**: Coroutine 1프레임 지연 + `Selectable.Select()` 호출.

```csharp
public void Show(...) {
    panelRoot.SetActive(true);
    StartCoroutine(SelectNextFrame(firstButton));
}

private IEnumerator SelectNextFrame(Selectable target) {
    yield return null;  // 1 frame 대기 — EventSystem refresh
    if (target != null && target.gameObject.activeInHierarchy) target.Select();
}
```

**Anti-pattern**:
- ❌ `EventSystem.current.SetSelectedGameObject(button.gameObject)` 직접 호출 (panel SetActive(true) 직후 1프레임 늦음)
- ❌ `button.Select()` panel 활성 *직전* 호출 (panel 비활성 → 무시)

---

### Rule 2: O 버튼 / Escape = popup / 다중 UI 닫기

**Why**: 게임패드 사용자가 popup 닫는 표준 방식. 모든 다중 UI 구성 시 의무.

**Pattern**: `EventSystem.InputSystemUIInputModule.cancel.action.performed` 구독.

```csharp
private InputAction _cancelAction;

void OnEnable() {
    var es = EventSystem.current;
    var module = es?.GetComponent<InputSystemUIInputModule>();
    if (module?.cancel != null) {
        _cancelAction = module.cancel.action;
        _cancelAction.performed += HandleCancel;
    }
}

void OnDisable() {
    if (_cancelAction != null) _cancelAction.performed -= HandleCancel;
}

private void HandleCancel(InputAction.CallbackContext ctx) {
    Hide(); // 또는 Dismiss / OnBackClicked
}
```

**변형 — 씬 root manager (popup 자체가 아님)**:
- popup 활성 여부 검사 후 close (예: `optionsPanel.activeSelf` true 시만)

---

### Rule 3: 게임패드 + KBM 동시 대응

**Why**: PC/콘솔 게임 = 2스킴 (또는 +터치). 어느 한쪽만 지원 시 사용자 부담.

**Action binding 의무**:
| Action | KBM | Gamepad |
|--------|-----|---------|
| Navigate | 화살표 키 | leftStick + dpad |
| Submit | Enter / Space | buttonSouth (Xbox A / PS ×) |
| Cancel | Escape | buttonEast (Xbox B / PS ○) |
| Click | Mouse leftButton | buttonSouth |

**EventSystem 의무**:
- `InputSystemUIInputModule.actionsAsset` = 게임의 InputActionAsset
- `m_MoveAction` / `m_SubmitAction` / `m_CancelAction` / `m_LeftClickAction` 4 ref 모두 set (UI map 의 action)

**Anti-pattern**: legacy `Input.GetKeyDown` 사용 / 마우스 클릭만 지원 / 게임패드만 지원

---

### Rule 4: UI 생성 default (TMP placeholder + 중앙 정렬 + Guardian 부착)

**TMP Text 자동 채우기 (빈 text 금지)**:
- Title text → "TITLE" 또는 패널 의도 명시 텍스트
- Button text → 버튼 라벨
- 동적 갱신 영역 → 초기 placeholder ("마지막 저장: -" 등) 또는 hidden

**버튼 / 타이틀 텍스트 중앙 정렬 (위아래좌우)**:
- `TMP_Text.alignment = TextAlignmentOptions.Center` (정수 514)
- RectTransform Stretch (anchorMin 0,0 / anchorMax 1,1 / sizeDelta 0,0)
- Pivot (0.5, 0.5)

**UIAutoSelectGuardian 부착** — Rule 5 참조.

---

### Rule 5 (최종): Device-aware auto-select

**Why**: "마지막 입력 장치" 판정의 함정 — `InputDevice.lastUpdateTime` 만으로 비교 시 *Gamepad 의 stick drift / device polling* 으로 매 프레임 갱신 → 마우스 사용 중에도 false positive.

**Pattern** — `InputSystem.onEvent` 콜백 + **significant input** deadzone:

```csharp
[RuntimeInitializeOnLoadMethod(BeforeSceneLoad)]
private static void InitTracker() {
    InputSystem.onEvent += (eventPtr, device) => {
        if (device is Gamepad gp && HasSignificantGamepadInput(gp))
            _lastGamepadTime = Time.unscaledTimeAsDouble;
        else if (device is Mouse || device is Keyboard)
            _lastMouseKbTime = Time.unscaledTimeAsDouble;
    };
}

private static bool HasSignificantGamepadInput(Gamepad gp) {
    if (gp.leftStick.ReadValue().sqrMagnitude > 0.04f) return true; // 0.2² deadzone
    if (gp.rightStick.ReadValue().sqrMagnitude > 0.04f) return true;
    if (gp.dpad.up.isPressed || /* ... */) return true;
    if (gp.buttonSouth.isPressed || /* ... */) return true;
    return false;
}

public static bool IsLastDeviceGamepad() => _lastGamepadTime > _lastMouseKbTime;
```

### 양방향 전환 처리 (Update 패턴)

```csharp
void Update() {
    var cur = EventSystem.current.currentSelectedGameObject;

    // 분기 1: 게임패드 → 마우스/KBM 전환 → 해제
    if (cur != null && !IsLastDeviceGamepad()) {
        EventSystem.current.SetSelectedGameObject(null);
        return;
    }
    // 분기 2: 이미 selected → 유지
    if (cur != null && cur.activeInHierarchy) return;
    // 분기 3: 마우스 → 게임패드 전환 + selected null → fallback.Select()
    if (IsLastDeviceGamepad() && fallback != null && fallback.gameObject.activeInHierarchy)
        fallback.Select();
}
```

**EventSystem.firstSelectedGameObject = null** (영구):
- 마우스로 시작 시 자동 select X (사장님 의도 정합)
- Guardian 이 device-aware 로 처리

---

## § 2 — Anti-pattern cluster (회귀 사고 기록)

### A1. Awake 안 `Hide()` 호출 = 자기 비활성 사고
```csharp
void Awake() {
    /* ... */
    Hide(); // ❌ 자기 SetActive(false) — Show() 처음 호출 시 Awake 후 비활성 → StartCoroutine 에러
}
```
**Fix**: 초기 비활성은 *Inspector* 의 `m_IsActive=0` 으로 보존. Awake 에서 SetActive(false) 호출 X.

### A2. Button targetGraphic 매핑 깨짐
- 사장님이 Button 의 `Transition` 변경 (예: Sprite Swap → Color Tint) 시 `targetGraphic` 자동 reset → *다른 button 의 Image* 로 fallback
- 결과: 다른 button hover 시 *이 button highlight*

**Fix**: 각 Button 의 `targetGraphic = self.Image` 명시 set.

### A3. EventSystem.SetSelectedGameObject 직접 호출 = 1프레임 무시
- Rule 1 의 Coroutine 패턴 사용 의무

### A4. Gamepad.lastUpdateTime 단독 비교 = stick drift false positive
- Rule 5 의 `InputSystem.onEvent + significant input` 패턴 사용 의무

---

## § 3 — UI Manager 신규 작성 체크리스트

신규 UI manager 작성 시 의무:

1. [ ] panel.SetActive(false) 는 *Inspector* 만 (Awake 에서 호출 X)
2. [ ] 모든 Button 의 `targetGraphic = self.Image` 명시
3. [ ] `UIAutoSelectGuardian` 컴포넌트 panel root 부착 + `fallback` Inspector 지정
4. [ ] Show / Open 메서드의 SelectXxxNextFrame Coroutine 에 `IsLastDeviceGamepad()` check
5. [ ] OnEnable/OnDisable 에 `cancel.action.performed += / -= HandleCancel` (Rule 2)
6. [ ] TMP Text 의 alignment = `TextAlignmentOptions.Center`
7. [ ] TMP Text 의 초기 text 는 placeholder 의무 (빈 text X)
8. [ ] EventSystem.firstSelectedGameObject = null (영구)
9. [ ] InputSystemUIInputModule.actionsAsset + 4 action ref 모두 set

---

## § 4 — 관련 자산 (이 플러그인 안)

- `templates/unity/UIAutoSelectGuardian.cs` — Rule 5 helper class (그대로 import 사용)
- `rules/ui-code.md` — Anti-pattern cluster + 추가 코딩 표준

## § 5 — 검증 시나리오 (모든 신규 UI 작성 시)

1. 게임패드만 사용 — 좌스틱 처음 누름 시 fallback.Select() 즉시 발화 (이동 X 보장)
2. 마우스만 사용 — 자동 select 발화 X / 마우스 hover button 만 highlight
3. 마우스 → 게임패드 전환 — 첫 게임패드 input 에 fallback select
4. 게임패드 → 마우스 전환 — currentSelected 즉시 해제 (highlight 잔존 X)
5. O 버튼 / Escape — popup / 다중 UI 닫기

위 시나리오 모두 통과해야 *production-ready UI*.
