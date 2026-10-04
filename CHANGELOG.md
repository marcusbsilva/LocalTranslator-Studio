# Changelog

## 2.2.0 — 2026-10-04

- Add browser-based installation, repair, catalogue refresh and confirmed removal on Models.
- Show background job progress, transfer size and operation logs.
- Update the server's configured languages after successful web operations.
- Add `--remove-languages` for Windows/Linux, including downloaded-archive cleanup.
- Preserve intentional default-language removals across future startup and repair.
- Protect management writes with same-origin checks and a current page token.
- Serialize web and CLI model operations with a cross-process lock.
- Add English and Brazilian Portuguese READMEs, twelve real screenshots, tests and GitHub CI configuration.

## 2.1.0 — 2026-10-04

- Add optional language installation, install-all and official catalogue refresh.
- Register additional successfully installed English bidirectional pairs.
- Validate German downloads, offline routes and automatic UI translation.

## 2.0.1 — 2026-10-04

- Translate after a 600 ms typing pause, with IME handling and a latest-input queue.
- Ignore stale results and keep the manual Translate shortcut.

## 2.0.0 — 2026-10-04

- Introduce the independent CTranslate2 runtime and English application pages.
- Add local Light/Dark themes, custom API Guide and native BAT/shell launchers.
