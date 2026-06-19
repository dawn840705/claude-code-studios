using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

/// <summary>
/// UI panel 의 자동 select fallback helper. 마지막 *실제* 입력 장치가 게임패드일 때만 fallback select.
///
/// 사용:
///   1. UI panel (popup / modal / main panel) 의 root GameObject 에 컴포넌트 부착
///   2. Inspector 의 `fallback` = panel 의 first selectable (예: 첫 Button)
///   3. EventSystem 의 InputSystemUIInputModule.actionsAsset + cancel action 설정
///
/// 동작:
///   - panel.SetActive(true) → OnEnable → Coroutine 1프레임 → IsLastDeviceGamepad 시 fallback.Select()
///   - Update — 마우스 → 게임패드 전환 시점에 fallback select / 게임패드 → 마우스 시점에 deselect
///
/// 의존: com.unity.inputsystem 1.x. uGUI (Canvas + Button).
///
/// 출처: dawn840705/claude-code-studios v0.3.0 — StarDiver 프로젝트 distillation.
/// 자세한 사양: docs/engine/unity-ui-guidelines.md
/// </summary>
public class UIAutoSelectGuardian : MonoBehaviour
{
    [Tooltip("마지막 입력 장치 = 게임패드일 때 자동 select 할 fallback Selectable.")]
    [SerializeField] private Selectable fallback;

    public void SetFallback(Selectable s) => fallback = s;

    void OnEnable()
    {
        StartCoroutine(InitialSelectIfGamepad());
    }

    private IEnumerator InitialSelectIfGamepad()
    {
        yield return null; // 1 frame 대기 — EventSystem refresh
        TrySelectIfGamepad();
    }

    void Update()
    {
        var es = EventSystem.current;
        if (es == null) return;
        var cur = es.currentSelectedGameObject;

        // 분기 1: 게임패드 → 마우스/KBM 전환 → 해제 (게임패드 highlight 잔존 제거)
        if (cur != null && !IsLastDeviceGamepad())
        {
            es.SetSelectedGameObject(null);
            return;
        }

        // 분기 2: 이미 selected → 유지
        if (cur != null && cur.activeInHierarchy) return;

        // 분기 3: 마우스 → 게임패드 전환 + selected null → fallback select
        TrySelectIfGamepad();
    }

    private void TrySelectIfGamepad()
    {
        if (!IsLastDeviceGamepad()) return;
        if (fallback == null || !fallback.gameObject.activeInHierarchy || !fallback.interactable) return;
        fallback.Select();
    }

    // === Static device tracker ===

    private static double _lastGamepadTime;
    private static double _lastMouseKbTime;
    private static bool   _initialized;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    private static void InitTracker()
    {
        if (_initialized) return;
        _initialized = true;
        InputSystem.onEvent += OnInputEvent;
    }

    private static void OnInputEvent(InputEventPtr eventPtr, InputDevice device)
    {
        if (device == null) return;

        if (device is Gamepad gp)
        {
            if (HasSignificantGamepadInput(gp))
                _lastGamepadTime = Time.unscaledTimeAsDouble;
        }
        else if (device is Mouse || device is Keyboard)
        {
            _lastMouseKbTime = Time.unscaledTimeAsDouble;
        }
    }

    private static bool HasSignificantGamepadInput(Gamepad gp)
    {
        if (gp.leftStick.ReadValue().sqrMagnitude  > 0.04f) return true; // 0.2² = 0.04 (deadzone)
        if (gp.rightStick.ReadValue().sqrMagnitude > 0.04f) return true;
        if (gp.dpad.up.isPressed    || gp.dpad.down.isPressed ||
            gp.dpad.left.isPressed  || gp.dpad.right.isPressed) return true;
        if (gp.buttonSouth.isPressed || gp.buttonNorth.isPressed ||
            gp.buttonEast.isPressed  || gp.buttonWest.isPressed)  return true;
        if (gp.leftShoulder.isPressed  || gp.rightShoulder.isPressed)  return true;
        if (gp.leftTrigger.ReadValue()  > 0.2f) return true;
        if (gp.rightTrigger.ReadValue() > 0.2f) return true;
        if (gp.startButton.isPressed || gp.selectButton.isPressed) return true;
        return false;
    }

    /// <summary>마지막 *실제* 입력 장치 = Gamepad 인지. Stick drift / device polling 무시.</summary>
    public static bool IsLastDeviceGamepad()
    {
        return _lastGamepadTime > _lastMouseKbTime;
    }
}
