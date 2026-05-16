# Unity Scene Loading Patterns — sceneLoaded 이벤트 함정

> **컨텍스트**: `SceneManager.sceneLoaded` 이벤트는 *이미 로드된 씬* 에는 발화 X. *단독 Play* (Editor 의 Play 버튼) 시 fade-in / 매니저 init 사고.

---

## § 1 — 함정

```csharp
class FadeManager : MonoBehaviour {
    void Awake() { overlay.alpha = 1f; } // 검정 시작
    void OnEnable() { SceneManager.sceneLoaded += HandleSceneLoaded; }
    void HandleSceneLoaded(Scene scene, LoadSceneMode mode) {
        StartCoroutine(FadeOut()); // 검정 → 투명
    }
}
```

**Boot.unity 진입 시** (정상):
1. Boot 씬 진입 → FadeManager.Awake → 검정 overlay
2. BootLoader.Start → `SceneManager.LoadSceneAsync("MainMenu", Additive)` → sceneLoaded 발화
3. HandleSceneLoaded → FadeOut → 정상 fade-in

**MainMenu 단독 Play 시** (사고):
1. MainMenu 씬 *이미 로드된 상태로 Play* → Awake/OnEnable 호출
2. FadeManager.Awake → 검정 overlay
3. `SceneManager.sceneLoaded` 이벤트 = **이미 로드된 씬에는 발화 X** → HandleSceneLoaded 호출 X
4. → 검정 overlay 유지 = **검은 화면**

---

## § 2 — Fix

`Start()` 메서드에서 *현재 active 씬* 에 대해 fade-in 자동 1회 발화. 단 *Boot 씬* 진입 시 skip (BootLoader 의 sceneLoaded 트리거에 위임 — 중복 발화 방지 = 검정→투명→검정 깜빡임 회피).

```csharp
void Start() {
    // Boot 씬 진입 시 = BootLoader 가 메인 씬 Additive 로드 후 sceneLoaded → 자동 fade-in 처리
    // MainMenu / Lobby / InGame 등 *단독 Play* 시 = sceneLoaded 미발화 → 여기서 자동 발화
    if (SceneManager.GetActiveScene().name == "Boot") return;
    StartCoroutine(FadeOut());
}
```

**대안**: BootLoader 안 `SceneManager.SetActiveScene(loaded);` 후 *수동* `FadeManager.Instance.FadeOut()` 호출. sceneLoaded 의존 X.

---

## § 3 — 일반화 패턴

매니저 / overlay / pre-loader 등 "씬 진입 시 자동 init" 의존 코드 = *단독 Play 정합* 점검 의무.

체크리스트:
1. `Awake()` 만으로 충분한가? (씬 진입 = Awake 항상 호출)
2. `Start()` fallback 필요한가? (sceneLoaded 의존이면 fallback 권장)
3. `BootLoader` 거치는 경우 vs 단독 Play 양쪽 시나리오 검증

---

## § 4 — 디버깅 단서

검은 화면 / overlay 잔존 / 매니저 init 안 됨 사고 시:
- `Debug.Log` 가 sceneLoaded handler 안 출력? = 미발화 의심
- BootLoader 거쳐서 정상 / 단독 Play 시 사고? = 본 함정 확정
- `Start()` fallback 추가 + active scene check 으로 fix
