# Validation — Local Translator Studio 2.2.0

Performed in the Linux VM on 2026-10-04 with Python 3.10.21. Actual dependency versions are recorded in requirements-linux-tested.txt.

## Independent translation pipeline

- Downloaded original model archives were reused; all 18 translation models were extracted and successfully loaded by CTranslate2.
- All 18 English bidirectional routes produced nonempty translations without subword-marker artifacts. Includes the Spanish → English BPE package and both Chinese variants.
- Automatic Chinese source detection and Chinese → English → Portuguese/Spanish/French routes passed.
- Language aliases zh, zh-CN, zt and pt-BR passed. Batch JSON and form-field requests passed.
- Empty text, same-language identity, leading/trailing spaces and blank lines were preserved.
- Invalid language/target/format, numeric text, oversized character count and oversized batch count were rejected with English HTTP 400 messages.
- All these API checks ran with outbound socket connections blocked. No model downloads or external services were needed by the running engine.
- Health, CORS preflight, model status and English page rendering with Accept-Language: pt-BR passed.
- Translation samples and timings are in validation-results.json. These are functional checks, not a comprehensive semantic quality benchmark.

## Installer

- Cached original archive checksum verification and extraction passed.
- Migration from previously extracted weights passed; the destination's model bytes matched the source.
- Runtime metadata contains only language pair and version fields. Model notices are preserved.
- Temporary-directory cleanup passed after both migration and installation.
- Archive traversal and Windows drive-path attempts were rejected.

## Browser and interface

Playwright Chromium tested actual Chinese → English → French translation and the displayed intermediate English text. Light/Dark switching persisted through navigation and reloads. All six page types used lang=en, and the GitHub link was present. The custom API tester returned HTTP 200. Pages were checked at 1280 px and 360 px; no mobile document overflow was found. No external frontend requests or JavaScript errors were observed. Screenshots are included for both themes, the API Guide and mobile layout.

## Automatic translation (2.0.1)

Browser checks passed for actual Chinese → English translation without a button click, automatic language changes to French and the English intermediate. Controlled request tests verified the 600 ms typing debounce, a single active request, stale-response suppression, clearing during an active request, IME composition handling, skipping an obsolete bridge's second leg and the immediate Translate button shortcut. Theme persistence and absence of JavaScript errors were also checked.

## Optional language installation (2.1.0)

- The official catalogue was fetched and parsed; 49 bidirectional non-English pairs were listed. The refresh command passed against the live catalogue.
- German → English and English → German archives were downloaded and installed using the independent pipeline. Repeating the install command reused installed models without downloads.
- Actual offline English → German, German → English and Chinese → English → German requests passed. German automatic source detection passed for a complete sentence. Neural quality is not guaranteed by these checks.
- The API language list, Models page and browser dropdown included German after restart. Automatic translation into German passed in Chromium.
- Controlled tests verified install-all selects 98 models (50 languages including English), an unavailable code is rejected before installation, and a failed optional pair does not enable that language or disable another successful pair.
- Optional-download tests verified recording the first HTTPS download's local hash, reusing a valid cache, repairing a corrupt cached archive and rejecting downloads that differ from an existing receipt.
- Existing typing debounce, stale-response suppression, single-request queue, clearing, IME composition and the manual shortcut passed again.
- The entire optional collection was not downloaded or tested in this VM. Archive compatibility is validated during installation, and a failing language remains disabled. Windows execution remains untested here.

## Web management and portfolio documentation (2.2.0)

- Real Chromium interaction removed German, cancelled a removal dialog without changes, downloaded and reinstalled both German routes, then translated English → German automatically. The manager updated without a server restart.
- Isolated management lifecycle tests passed: current-page token enforcement, cross-origin and foreign Host rejection, English removal rejection, background removal, cached-archive deletion, persistent default-language exclusion/reinstallation, live language registry reload, concurrent job rejection and process-lock contention.
- Twelve real screenshots cover Translate, Models, API Guide, About, Licenses and the error page in both themes. Desktop captures were inspected; all page types passed 360 px overflow checks without JavaScript errors.
- English README.md and Brazilian Portuguese readme-ptbr.md include web management, Windows and Linux command examples, screenshot links, upgrade guidance, API use and actual validation limits.
- GitHub ignore/line-ending rules, contribution notes, changelog and a lightweight Linux CI workflow are included. The workflow itself has not been run on GitHub.

## Packaging and platform scope

The full dependency graph resolved for Windows x64 / Python 3.10 (22 packages). The Windows BAT was reviewed; the Linux shell passed syntax checking and Python files compiled. Actual Windows runtime execution has not been performed in this Linux VM.

The delivery ZIP excludes virtual environments, translation archives, extracted weights and obsolete source files. It contains the independent application source, English documentation, local fonts and required notices. Model archives remain portable and are downloaded or reused during setup. Neural outputs can differ from earlier software because sentence segmentation and preprocessing are now handled by the independent pipeline.
