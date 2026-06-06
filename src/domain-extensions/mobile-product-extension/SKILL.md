---
name: mobile-product-extension
description: Adds professional product rules for Android, iOS, and cross-platform mobile app changes involving offline state, push notifications, app lifecycle, permissions, privacy prompts, background execution, platform differences, and release-store constraints.
license: MIT
changeforge_kind: domain-extension
changeforge_version: 0.1.0
---

## Mission
Extend ChangeForge product and code change analysis with mobile engineering discipline for app lifecycle correctness, offline-first data integrity, platform security model compliance (iOS/Android), App Store/Play Store release constraints, accessibility requirements, push notification reliability, and performance budgeting on constrained mobile hardware — ensuring that mobile changes work correctly across network conditions, app states, OS versions, and device capabilities without causing data loss, store rejection, or privacy violations.

## Trigger Signals
- Any change to iOS (Swift/SwiftUI/Obj-C) or Android (Kotlin/Java/Jetpack Compose) application code.
- React Native or Flutter cross-platform feature changes.
- Changes to device permission request flows: camera, microphone, location (always/when-in-use), contacts, notifications.
- Push notification handling changes: APNS configuration, FCM configuration, notification categories, deep link routing.
- Offline-first or sync logic changes: local database (Room, Core Data, SQLite), conflict resolution, sync queue.
- App lifecycle changes: background task scheduling, foreground service additions, scene state handling.
- Mobile security changes: biometric authentication, Keychain/Keystore usage, certificate pinning.
- App Store or Play Store submission preparation, version configuration, or privacy manifest changes.
- Deep link and Universal Link / App Link configuration changes.
- Performance-sensitive changes: list rendering, image loading, animation, main-thread blocking.

## Do Not Use When
- The change is a pure web frontend change with no native mobile code, no React Native component, and no mobile-specific behavior.
- The change is a backend API change with no mobile client impact.

## Non-Negotiable Rules
- **Offline behavior must be an explicit first-class design decision**: a mobile app that fails silently or loses user data when connectivity is lost has failed its most fundamental mobile requirement — define the offline state, pending queue, and sync resolution for every user-facing operation.
- **App lifecycle transitions must be explicitly handled**: iOS apps are suspended and terminated without warning; Android apps are killed in low-memory conditions — every stateful view must save its state on `onPause`/`sceneWillResignActive` and restore on resume; no work-in-progress can be lost on lifecycle transition.
- **Permission denial is a required product flow, not an error path**: `camera: denied`, `location: denied`, `notifications: denied` are expected user choices — design the permission-denied UX before implementing the feature; never assume permission is granted.
- **Main thread must not be blocked**: any work that blocks the main thread for > 16ms causes a dropped frame (jank); network calls, disk I/O, and JSON parsing must be on background threads — use async/await (Swift), coroutines (Kotlin), or background queues (DispatchQueue).
- **Keychain (iOS) and Keystore (Android) are mandatory for sensitive credentials**: storing tokens, API keys, or biometric-protected data in `UserDefaults`, `SharedPreferences`, or plain `AsyncStorage` is a security violation — these are accessible to any process that can read the app sandbox.
- **Version compatibility must be maintained for rolling deployments**: the API contract must support the oldest supported app version still in production — breaking API changes must be phased using API versioning or feature flags, not simultaneous server + client deployment.
- **Privacy manifest (iOS 17+) and Data Safety section (Play Store) must be accurate**: inaccurate privacy declarations cause App Store rejection and regulatory liability — declare all accessed APIs and data collected.
- **Accessibility is not optional**: iOS VoiceOver and Android TalkBack users represent a legally protected user class (ADA, WCAG 2.1 AA) — all new screens must have `accessibilityLabel`, correct focus order, and sufficient contrast ratio.

## Industry Benchmarks
- **Apple Human Interface Guidelines (HIG)**: Navigation patterns, control sizing (minimum 44×44pt tap target), typography, color contrast, and adaptive layout. The authoritative source for iOS design decisions.
- **Android Design Guidelines (Material Design 3)**: Component library, elevation, color system, dynamic color, navigation patterns, touch target sizing (48dp minimum).
- **OWASP MASVS (Mobile Application Security Verification Standard)**: Level L1 (basic security) and L2 (defense-in-depth). MASVS-STORAGE, MASVS-CRYPTO, MASVS-AUTH, MASVS-NETWORK. The security standard for mobile applications.
- **Core Web Vitals (for mobile web / React Native)**: LCP, FID/INP, CLS. Applies to React Native's performance measurement (Interaction to Next Paint for touch responsiveness).
- **Firebase Performance Monitoring / Xcode Instruments**: Profile cold start time (target < 400ms to first useful frame), memory footprint, battery consumption, and main thread blocking.
- **App Store Review Guidelines (Apple)**: Section 2 (Performance: crashes, completeness), Section 5 (Legal: privacy, permissions). The canonical source of rejection causes.
- **Google Play Policy (Android)**: Target API level requirements, dangerous permissions policy, privacy policy requirements for apps targeting children.
- **APNS / FCM Best Practices**: Notification payload size limits (4KB APNS, 4KB FCM data message), priority levels (high vs. normal), collapse key behavior, notification grouping, Time To Live (TTL) settings.

### Mobile Platform Security Controls Matrix

| Security Requirement | iOS Implementation | Android Implementation |
|---|---|---|
| Secure credential storage | Keychain with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` | Android Keystore with `StrongBoxBacked=true` |
| Biometric authentication | LocalAuthentication framework (`LAContext`) | BiometricPrompt API (`BiometricManager`) |
| Certificate pinning | `NSURLSession` with custom `URLSessionDelegate` | `OkHttp CertificatePinner` or Network Security Config |
| Jailbreak/root detection | Runtime integrity check (limited; jailbreaks bypass) | SafetyNet Attestation / Play Integrity API |
| Transport security | `NSAppTransportSecurity` (ATS enforced) | Network Security Config (cleartext blocked by default API 28+) |
| Sensitive data in memory | Zero sensitive buffers after use; disable screenshot in app switcher | `FLAG_SECURE` on windows; clear sensitive buffers after use |

## Domain Risk Model
- **Data loss on lifecycle transition**: user fills a long form; the OS kills the app in low-memory; no state was saved; user returns to an empty form.
- **Permission denial blocks core feature without UX guidance**: user denies camera permission; the app shows a crash or empty state instead of explaining how to enable permission in settings.
- **Token stored in SharedPreferences readable by backup**: Android backup enabled by default; `SharedPreferences` with auth token backed up to Google Drive; token readable by restoring to another device.
- **Push notification routes to wrong screen**: deep link in notification payload uses a path that no longer exists after a navigation refactor; notification tap crashes or navigates to app root.
- **API breaking change breaks older app versions**: backend deploys a breaking change to a JSON field; old app versions still in production parse the new response incorrectly; users on old versions experience crashes.
- **Main thread I/O causes ANR (Android) or watchdog termination (iOS)**: a database query runs on the main thread; on a slow device with a large database, it takes 5 seconds; Android reports ANR; iOS terminates the app.
- **Biometric bypass via keystore downgrade**: biometric authentication implementation does not use `setUserAuthenticationRequired(true)` on the keystore key — an attacker can access the keystore without biometric verification.
- **App Store rejection due to undeclared API usage**: an SDK used by the app calls privacy-sensitive APIs (tracking, location) that are not declared in the iOS 17 Privacy Manifest — rejected on first review.

## Linked Foundation Capabilities
- interaction-state-modeling
- state-management-design
- frontend-api-integration
- permission-boundary-modeling
- version-compatibility
- regression-testing
- observability
- error-code-design
- performance-budgeting
- authentication-security

## Linked Professional Skills
- experience-impact-modeler
- frontend-change-builder
- backend-change-builder
- data-api-contract-changer
- reliability-observability-gate
- quality-test-gate
- delivery-release-gate
- security-privacy-gate

## Critical Details
- **Cold start time is the most critical mobile performance metric**: users judge app quality in the first 3 seconds — profile cold start with Xcode Time Profiler / Android Startup Profiler; defer non-critical initialization off the main thread.
- **Background fetch and BGTask (iOS) have execution time limits**: BGProcessingTask has ≈ 30 seconds; BGAppRefreshTask has ≈ 30 seconds; work that exceeds the budget is terminated by the OS without warning — design background work to be interruptible and resumable.
- **Android WorkManager is the correct API for guaranteed background work**: `AsyncTask` is deprecated; raw background threads are killed; `Service` requires foreground notification for long work — use WorkManager for any background work that must complete even if the app is killed.
- **Notification permission requires a value proposition**: iOS 12+ requires explicit `UNUserNotificationCenter.requestAuthorization` call; Android 13+ requires `POST_NOTIFICATIONS` runtime permission — present the permission request after demonstrating value, not on first app launch.
- **React Native bridge performance**: frequent synchronous calls across the React Native bridge (legacy architecture) cause jank — migrate hot paths to Fabric/JSI for synchronous access; avoid large JS thread blocking operations.
- **App size budget**: initial download size affects install conversion rate; iOS App Thinning and Android App Bundle reduce download size — target < 50MB download for iOS cellular download limit; split APKs by ABI and density.

### Anti-Examples

| Mobile Pattern | Problem | Corrected Approach |
|---|---|---|
| `UserDefaults.set(authToken, forKey: "token")` | Token in UserDefaults included in iCloud backup; not hardware-protected | Use Keychain with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| `URLSession.shared.dataTask(completionHandler: { data in DispatchQueue.main.sync { ... } })` | Deadlock if called on main thread | `DispatchQueue.main.async { ... }` or use `@MainActor` with async/await |
| Navigation on notification tap hardcodes path `/home/notifications` | Path invalid after navigation refactor; crash on tap | Validate deep link path before navigation; handle unknown paths gracefully |
| API response removes a field; old app still in production | Old app crashes parsing new response | Maintain backward-compatible API until old version EOL; use optional fields |
| Request camera permission on app launch | User has no context; denial rate high | Request permission at the point the feature is first needed; explain why |

## Failure Modes
- **Sync conflict causes data loss**: two devices edit the same record offline; sync conflict resolution uses last-write-wins without user notification; one edit is silently discarded.
- **App killed during background sync**: iOS kills background task after 30 seconds; partial sync leaves data in inconsistent state; no retry mechanism; user data appears missing until next full sync.
- **Store rejection delays critical release**: privacy manifest missing required `NSUserDefaults` usage declaration; App Store review rejects binary; fix requires a new build and re-review cycle (1–3 days).
- **Biometric authentication bypass**: Keystore key created without `setUserAuthenticationRequired(true)` — key accessible without fingerprint; security claim violated.
- **Push notification tap lands on wrong screen after navigation refactor**: 15% of notification-originated sessions crash on launch because the deep link target screen was removed; crash rate spike on release day.
- **ANR on older devices**: database query on main thread takes 8 seconds on a low-end device with 100K records; Android reports ANR; 3-star reviews spike.

## Output Contract
Return mobile change assessment with:
- **Lifecycle and offline model**: state preservation on lifecycle transitions, offline pending queue, sync conflict resolution strategy.
- **Permission flow design**: granted UX, denied UX, system settings deep link for each requested permission.
- **Platform compatibility matrix**: iOS version range, Android API level range, tested device categories.
- **Security review**: credential storage location, certificate pinning, biometric authentication correctness, privacy manifest accuracy.
- **Push notification routing**: deep link validation, notification category mapping, stale notification handling.
- **Performance profile**: cold start time, main thread blocking audit, memory footprint, battery impact.
- **Store submission readiness**: privacy manifest completeness, Data Safety section accuracy, App Review guideline compliance.
- **Version compatibility**: oldest supported app version compatibility with the backend change.
- **Block/pass decision** with required conditions for approval.

## Evidence Contract
Close a mobile change only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`), because a shipped binary cannot be hot-fixed:
- **Basis**: the platform lifecycle rule, permission policy, or store guideline the change rests on.
- **Files and boundaries inspected**: the lifecycle transitions, offline queue, and push path read, with the Android/iOS platform difference and the oldest-supported-version boundary confirmed.
- **Placement rationale**: why state preservation, offline-conflict resolution, and permission-degradation UX live where they do.
- **Validation commands**: the lifecycle/backgrounding test, offline-sync-conflict test, permission-denied walkthrough, and push-delivery check run on the device matrix, each with its outcome.
- **Residual risk**: the deep-link, background-execution-limit, version-skew, or store-review path that remains, with the named owner and the staged-rollout gate.

## Quality Gate
1. Offline state and sync conflict resolution are explicitly designed and tested.
2. App lifecycle transitions (background, foreground, terminate) are handled; state is preserved and restored.
3. Permission-denied UX is designed and tested for all requested permissions.
4. All sensitive credentials use Keychain (iOS) or Keystore (Android) — not UserDefaults/SharedPreferences.
5. Certificate pinning is configured for all production API connections.
6. Notification deep links are validated before navigation; unknown paths are handled gracefully.
7. Main thread blocking is absent; async/await or coroutines are used for I/O.
8. Privacy manifest (iOS) and Data Safety section (Android) are accurate and complete.
9. Accessibility labels, focus order, and contrast ratio pass automated and manual VoiceOver/TalkBack review.
10. Backend API change maintains compatibility with oldest supported app version.

## Handoff
- **security-privacy-gate** — for OWASP MASVS compliance, credential storage, certificate pinning, and privacy manifest.
- **experience-impact-modeler** — for permission request UX, permission-denied flows, and accessibility review.
- **quality-test-gate** — for device matrix test requirements, lifecycle test, offline test, and biometric bypass test.
- **delivery-release-gate** — for App Store/Play Store submission, phased rollout, and version compatibility.
- **backend-change-builder** — for API backward compatibility with older app versions.

## Completion Criteria
The mobile change is approved when offline state is explicitly designed, app lifecycle transitions preserve state, permission-denied UX is implemented, credentials use platform secure storage, certificate pinning is configured, push notification deep links are validated, main thread is unblocked, privacy manifest and Data Safety section are accurate, accessibility requirements are met, and backend API maintains compatibility with the oldest supported app version.
