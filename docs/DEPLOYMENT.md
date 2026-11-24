# Deploying HealthMate

This guide takes HealthMate from your computer to a public website on your own
domain, with HTTPS.

## 1. Why Render?

| Need | Render web service |
|---|---|
| Runs Flask and Python | Yes: a normal Python server running `gunicorn app:app` |
| Keeps data safe | Yes: the app stores nothing on the server, and all user data lives in Firestore, so restarts and redeploys lose nothing |
| Works with Firebase | Yes: the browser talks to Firebase directly |
| Custom domain and HTTPS | Yes: free certificates, renewed automatically |
| Simple to explain | Yes: "GitHub push → Render builds → gunicorn runs Flask" |

**Free plan:** the service sleeps after 15 minutes without visitors and takes
about a minute to wake. That's fine for a project, but for the demo either
open the site a few minutes early or switch to the paid **Starter** plan for
that month. Check Render's pricing page for the current cost.

Alternatives considered: Vercel (Flask runs as serverless functions, which is
harder to explain), PythonAnywhere (custom domains need a paid plan), Firebase
Hosting plus Cloud Run (more setup).

## 2. Who does what

| Where | Done by | Actions |
|---|---|---|
| **Code** (already done) | Claude | `render.yaml`, `gunicorn.conf.py`, pinned `requirements.txt`, production settings (`APP_ENV`), security headers, `/healthz` health check, logging |
| **GitHub** | You (or Claude with your OK) | Push the code to `github.com/todo4486/healthmate` |
| **Firebase console** | You | Project, web app config, sign-in methods, authorised domains, Firestore, rules |
| **Render** | You | Account, create the service, add the custom domain |
| **Domain registrar** | You | Buy the domain, add the DNS records Render gives you |

## 3. Before you deploy (checklist)

- [ ] `venv/bin/python -m pytest -q`: all tests pass.
- [ ] Firebase steps 1–7 in the README are done, and `static/js/firebase-config.js`
      contains your four values.
- [ ] `firestore.rules` is **published** (Firebase → Firestore → Rules shows it).
- [ ] You tested sign-up, login, habits and a saved symptom check locally.
- [ ] Everything is committed and pushed to GitHub (`git status` is clean).

## 4. Deploy on Render

1. Sign up at https://render.com and connect your GitHub account when asked.
2. **New → Blueprint** → choose the `healthmate` repository → **Apply**.
   Render reads `render.yaml`:
   * build: `pip install -r requirements.txt`
   * start: `gunicorn app:app`
   * health check: `/healthz`
   * environment variable: `APP_ENV=production`
   * Python version: from `.python-version` (3.11)
3. Wait for the first deploy to say **Live** (a few minutes). Open the
   `https://healthmate-xxxx.onrender.com` address Render shows.
4. **Firebase → Authentication → Settings → Authorized domains → Add domain**:
   add that `healthmate-xxxx.onrender.com` address. Without it, Google sign-in
   fails with "Sign-in isn't allowed from this web address yet".

From now on, every push to `main` redeploys automatically.

## 5. Connect your custom domain

You need a domain from a registrar (e.g. GoDaddy, Namecheap, Hostinger,
Google Domains' successor Squarespace, or Cloudflare).

1. **Render** → your service → **Settings → Custom Domains → Add**. Add both
   `yourdomain.com` and `www.yourdomain.com`. Render shows the DNS records
   to create. **Always use the values Render shows you**; they are the source
   of truth.
2. **At your registrar's DNS settings**, typically:

   | Type | Name / Host | Value |
   |---|---|---|
   | `CNAME` | `www` | `healthmate-xxxx.onrender.com` |
   | `ALIAS` or `ANAME` (if offered) | `@` | `healthmate-xxxx.onrender.com` |
   | otherwise `A` | `@` | `216.24.57.1` (Render's address; confirm in Render) |

   * Delete any other `A` records on `@`, and any `AAAA` records (Render doesn't
     use IPv6 addresses, and they can stop verification).
   * Using Cloudflare? Set the record to **DNS only** (grey cloud) until Render
     has issued the certificate.
3. Back in Render, click **Verify**. DNS changes can take from a few minutes up
   to 24–48 hours.
4. Once verified, Render issues the HTTPS certificate automatically.
5. **Firebase → Authorized domains**: add `yourdomain.com` and `www.yourdomain.com`.
6. *(Recommended)* Add the same domains to the API key's website restrictions
   (README, Firebase step 8).

## 6. Check HTTPS

- [ ] `https://yourdomain.com` shows a padlock. Click it to confirm the
      certificate is valid and issued for your domain.
- [ ] `http://yourdomain.com` (without the s) redirects to `https://`.
      Render does this automatically.
- [ ] `https://www.yourdomain.com` works, or redirects to your main domain.
- [ ] `https://yourdomain.com/healthz` shows `{"app":"HealthMate","status":"ok"}`.
- [ ] Optional: run https://www.ssllabs.com/ssltest/ on your domain and aim for grade A.
- [ ] Optional: check the headers at https://securityheaders.com.

## 7. Test the live site

Use a desktop browser **and** your phone. Use a test account, not your main one.

| Area | Test | Expected |
|---|---|---|
| Home | Open the site | Page loads, no errors in the browser console (F12) |
| Register | Sign up with a new email | Lands on the Dashboard, "Hello, <name>" |
| Register | Same email again | "An account with this email already exists" |
| Logout | Click Log out | Back on Home; header shows Log in / Sign up |
| Login | Wrong password | "Email or password is incorrect." |
| Login | Correct password | Dashboard |
| Google | Continue with Google | Google popup, then Dashboard |
| Reset | Reset password | "If an account exists… we've sent a link"; email arrives |
| Protected | Log out, open `/habits` | Sent to the login page, then back to Habits after login |
| Habits | Add "Drink water", Hydration | Card appears; progress 0 of 1 |
| Habits | Empty name | "Enter a name for your habit." |
| Habits | Tick, then untick | Progress goes to 100% and back to 0% |
| Habits | Refresh the page | Habits and ticks are still there |
| Habits | Delete, confirm | Card disappears |
| Dashboard | Tick a habit on the Dashboard | Habit Tracker shows it ticked too |
| Symptoms | Tick "Chest discomfort" | "Get medical help now" |
| Symptoms | Cough, mild, 1–3 days, 18–64 | "Self-care may be enough for now" with when-to-get-help |
| Symptoms | Save to my history | Appears on the Dashboard; can be deleted |
| Assistant | Each suggested question | A topic answer |
| Assistant | "I have chest pain" | Urgent safety message with 112 |
| Library | Open a category and an article | Pages load; breadcrumb works |
| Safety | Tap 112 on a phone | Phone dialler opens with 112 |
| Mobile | Menu button, Emergency link | Menu opens and closes; Emergency always visible |
| Isolation | Log in as a second account | None of the first account's habits or checks are visible |
| Persistence | Firebase → Firestore → Data | `users/<uid>/habits` etc. contain your test data |

## 8. If something goes wrong (recovery)

| Problem | What to do |
|---|---|
| A new deploy broke the site | Render → service → **Events** → find the last good deploy → **Rollback**. Then fix the code and push again. |
| Bad code is on GitHub | `git revert <commit>` then `git push`; Render redeploys the reverted version. |
| Rules change locked users out | Firebase → Firestore → Rules → the history list → restore the previous version → Publish. Keep `firestore.rules` in Git as the master copy. |
| Sign-in fails on the live site | Check that the domain is in Firebase's authorised domains and in the API-key restrictions. |
| "Permission denied" when saving | The rules aren't published, or differ from `firestore.rules`. Publish them again. |
| Site slow to open | Free plan waking up (about a minute). Wait, or upgrade the plan. |
| Need logs | Render → service → **Logs** (gunicorn requests and Python errors). |

Firestore holds all user data and is managed by Google, so a broken deploy or
rollback never deletes data.

## 9. Deployment checklist (summary)

- [ ] Tests pass locally
- [ ] Firebase config filled in; sign-in methods enabled
- [ ] Firestore created; **rules published**
- [ ] Code pushed to GitHub
- [ ] Render Blueprint deployed and **Live**
- [ ] Render address added to Firebase authorised domains
- [ ] Custom domain added in Render; DNS records created; verified
- [ ] HTTPS padlock; http redirects to https
- [ ] Custom domain added to Firebase authorised domains (and API-key restrictions)
- [ ] Live test table (section 7) completed on desktop and phone
- [ ] Before the demo: open the site a few minutes early (free plan), or upgrade
