# HealthMate: QA and Security Report

**Date:** 24 November 2026 · **Result:** 213 of 213 automated tests pass ·
**Status:** ready to deploy, once the Firebase steps are done and real-account
tests are run (see "Manual actions").

## 1. Scope

Reviewed: all routes; registration, login, logout and Google sign-in; Firebase
configuration; Firestore rules and user data isolation; Habit Tracker;
Dashboard; Symptom Guide; Wellness Assistant; Health Library; Safety Center;
form validation; error, loading and empty states; responsive layout and mobile
navigation; XSS; redirects; environment variables and secrets; production
configuration; broken links; browser console; Python errors; performance.

## 2. Issues found and fixed

| # | Area | Issue | Severity | Fix |
|---|---|---|---|---|
| 1 | Auth | `auth.js` loaded twice (once with `?v=`), creating two separate copies, so the sign-up redirect pause and logout could misbehave | High | Removed version suffixes; static files are now revalidated (`Cache-Control: no-cache`) |
| 2 | Security | Open redirect: `?next=/..//evil.com` was tidied by the browser into `//evil.com` (another site) | High | Re-check the tidied path; 14 attack patterns tested |
| 3 | Security | No Content-Security-Policy or security headers | Medium | Added CSP (nonce for our only inline script), `X-Frame-Options`, `nosniff`, Referrer-Policy, Permissions-Policy, COOP, and HSTS in production |
| 4 | Symptom Guide | Chest pain without the word "severe", and negated text ("no fever"), were mishandled in the old project's approach | High | Explicit warning-sign question; chest and breathing problems always urgent; free text can only *add* caution |
| 5 | Habits | Ticks saved to the wrong day if the page stayed open past midnight | Medium | Habit pages reload just after midnight |
| 6 | API | Wrong-method (405) errors on `/api/` returned an HTML page | Low | App-wide error handlers reply in JSON for `/api/` |
| 7 | Production | Behind Render's proxy Flask would think requests were plain HTTP | Medium | `ProxyFix` in production (tested) |
| 8 | Production | Server errors were not logged | Medium | 500 handler logs the error; logs go to the console for Render |
| 9 | Production | Only top-level packages pinned | Low | All 9 production packages pinned; clean install tested |
| 10 | Forms | Habit form error message never appeared (ID mismatch) | Medium | Fixed, plus a test that every form's error labels match its fields |
| 11 | UI | Symptom form steps showed stray numbered circles (CSS class clash with the landing page) | Low | Renamed the form's classes |
| 12 | UI | Warning-signs legend overlapped the box border | Low | Moved the box styling inside the fieldset |
| 13 | UI | Results scrolled under the sticky header | Low | `scroll-padding-top` |
| 14 | UI | Stale CSS after changes | Low | Same fix as #1 |
| 15 | Content | Emergency numbers needed verifying | Medium | Verified 112 (MHA ERSS), 108 (NHM, most states), Tele-MANAS 14416 / 1-800-891-4416 (MoHFW); "last checked" date shown |
| 16 | Code | Unused macro and 5 unused CSS rules | Low | Removed |
| 17 | Noise | Browsers' `/favicon.ico` requests returned 404 | Low | Redirect to the logo |

## 3. Security review

| Check | Result |
|---|---|
| Firestore rules | Default deny. Every path is under `users/{uid}` and requires `request.auth.uid == uid`. Writes allow only listed fields with type, length and allowed-value checks; timestamps must be the server time. Habits and saved checks can't be edited, only created or deleted. |
| Rules deployed? | **Not verified.** They are in `firestore.rules` and must be published by you (README, step 7). |
| Client vs server protection | Documented clearly: page hiding in `auth.js` is UX only; the rules are the real security. |
| Secrets | None in the repository (automated scan). The Firebase web config is public by design. `.env` and service-account files are git-ignored. |
| XSS | Jinja auto-escaping (no `|safe`); JavaScript uses `textContent` only (automated check: no `innerHTML =`, `insertAdjacentHTML`, `eval`); CSP blocks injected scripts. Tested by typing HTML into the chat, habit and symptom forms. |
| Redirects | `safeNextPath` allows same-site paths only (14 cases tested in the browser). |
| Input validation | Server re-validates everything (types, allowed values, lengths); 16 KB body limit; tested with malformed, empty, oversized and non-JSON input. |
| Privacy | First name only; descriptions, warning-sign answers and chats are never stored; symptom saving is opt-in and deletable. |

## 4. Tests executed

### Automated (pytest): 213 passed, 0 failed

| File | Tests | Covers |
|---|---|---|
| `test_symptom_engine.py` | 68 | Every warning sign → urgent; chest and breathing urgent at every severity and duration; text can't lower a result; negation still cautious; whole-word matching; under-5s and "other" never self-care; doctor rules; 19 malformed or empty inputs; no free text in saved data; no diagnosis wording |
| `test_pages.py` | 44 | Every page loads with layout, access level, nav, data-driven content, field-error wiring, no inline styles, caching headers, 404/500 pages |
| `test_assistant.py` | 32 | 5 suggested questions; custom questions; emergencies and crises get safety replies (and win over topics); no medicines or diagnosis; fallback; empty/long/wrong-type input; links valid |
| `test_library.py` | 26 | 6 required categories; each category page shows only its articles; every article page; empty state; 404s; no medical-advice wording |
| `test_security.py` | 26 | Headers and CSP; nonce per request; HSTS only in production; proxy HTTPS; debug off; secret scan; `.gitignore`; crawl of every internal link; no unsafe HTML insertion in JS; no autoescape bypass |
| `test_api.py` | 17 | Structured results; 400s for bad answers, non-JSON and broken JSON; 405 and 404 in JSON; 413 for oversized requests |

### Manual and browser tests (desktop 1280 px, tablet 768 px, phone 375 px)

| Area | Result |
|---|---|
| Every page at three widths: no sideways scrolling, including long unbroken text | Pass |
| Mobile menu opens and closes (and Escape); Emergency link always visible | Pass |
| Browser console on all 12 page types | No errors |
| CSP: inline script runs, Firebase SDK and Firestore module load from Google's CDN | Pass |
| Symptom Guide: validation, urgent, doctor and self-care results, HTML in description shown as text, "Start again" | Pass |
| Assistant: suggestions, typing indicator, input disabled while waiting, urgent reply, connection-error bubble, empty message ignored | Pass |
| Library: categories, articles, breadcrumbs | Pass |
| Habit dialog: open, validation, Escape, error banner | Pass |
| Signed-out visitor on `/dashboard` or `/habits` → `/login?next=…` (with test Firebase config) | Pass |
| Production server (gunicorn, `APP_ENV=production`): health check, headers incl. HSTS, API, 404 | Pass |
| Clean install of `requirements.txt` + `pip check` | Pass |

### Not yet tested (needs your Firebase project)

Real registration, login, wrong password, Google sign-in, logout, password-reset
email, creating, ticking, unticking, deleting and refreshing habits, saving and
deleting symptom checks, dashboard sync, isolation between two accounts, and
the published rules. These flows are written and code-reviewed, and the live
test table in `docs/DEPLOYMENT.md` (section 7) covers each of them.
**Run it once Firebase is set up.**

## 5. Remaining limitations

* The Symptom Guide and Assistant are rule-based, deliberately cautious, and
  not medical tools. Free-text matching causes false alarms (by design, never
  false reassurance).
* Firestore rules can't cap the number of habits per user (the app caps at 20).
* `habitLogs` list entries aren't type-checked individually (Firestore rules
  can't loop over lists); the list size is capped at 50.
* "Today" follows the device clock and time zone.
* Free Render plan sleeps after 15 minutes idle (about a 1-minute wake).
* If you later use a custom `authDomain` instead of `*.firebaseapp.com`,
  add it to `FIREBASE_FRAMES` in `security.py`.
* Firebase rules can't be unit-tested on this computer without Java (for the
  Firebase emulator); isolation is verified by review and the manual test.

## 6. Manual actions you must perform

1. Complete Firebase steps 1–8 in the README, especially **publishing
   `firestore.rules`**.
2. Run the live test table (`docs/DEPLOYMENT.md`, section 7) with two test accounts.
3. Push to GitHub, deploy on Render, and connect your domain (`docs/DEPLOYMENT.md`).
4. Add the Render address and your domain to Firebase's authorised domains.
