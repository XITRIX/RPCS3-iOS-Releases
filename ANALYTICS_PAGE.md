# Public performance page

The buildless site lives in `docs/`. It publishes **aggregate** device/game/mode/thermal measurements, not user IDs, event logs or Crashlytics reports. No credentials or Analytics SDK are shipped to visitors.

The seed snapshot was exported from the existing Google Analytics exploration on 25 October 2026, covering 25 September through 25 October inclusive: **82 device/game combinations, 75 title IDs, 24 hardware models, 65,954.80494 measured seconds**. It contains JIT results only because that exploration has an exact JIT filter. API refreshes keep JIT and interpreter measurements separate and request all available history through today in the property's timezone. The query starts on 14 August 2015, before GA4 and this property's collection, so it includes all available gameplay measurements. No historical data is invented or recovered if Google no longer retains it. Omit --days for this default; an optional --days 1–90 still supports manual rolling reports.

## Publish on GitHub Pages

This is an independent website branch (`game-performance-dashboard`), with no release-branch history or README. Select **Settings → Pages → Build and deployment → Source: GitHub Actions**. Run the **Performance page** workflow, or let a site-file push run it. The expected URL is `https://xitrix.github.io/RPCS3-iOS-Releases/`; only a successful deployment establishes that it is live.

The workflow validates changes in pull requests. Production runs deploy only `docs/`. The workflow declares a **07:17 UTC** daily refresh and supports manual runs. GitHub runs scheduled workflows only on the repository default branch: while `main` remains the default, this independent branch needs an external scheduled dispatch or a small scheduler on the default branch. The daily refresh is not active merely by pushing this branch. The dated seed can be deployed before Google credentials are configured; a scheduled run without credentials fails visibly rather than claiming an update.

## Connect the daily Google Analytics refresh

Use GA4 property **558536976** (`rpcs3-ios`). Enable the **Google Analytics Data API** for the chosen Google Cloud project. Give a dedicated service account **Viewer** access to this Analytics property in **Analytics → Admin → Property access management**. Firebase IAM access alone does not grant Analytics report access.

Choose one authentication route:

1. **Workload Identity Federation (preferred):** configure a Google Cloud identity provider restricted to this repository and its `game-performance-dashboard` branch. Add repository variables `GA_WORKLOAD_IDENTITY_PROVIDER` (the full provider resource name) and `GA_SERVICE_ACCOUNT` (the Viewer service-account email). Grant that repository identity permission to impersonate only this service account. The workflow uses the short-lived GitHub OIDC identity.
2. **Service-account key:** store the complete JSON key in the repository's Actions secret **`GA_CREDENTIALS_JSON`**. Never commit the key, paste it into an issue, or place it in `docs/`. The workflow writes temporary authentication material outside the published directory and removes it through the auth action's cleanup.

These grants must be configured by the owner; the page does not create accounts, expand access or obtain credentials. No account credentials were added as part of the static-page implementation. See [Google's authentication action](https://github.com/google-github-actions/auth) and [Analytics custom fields](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema).

The exporter reads the registered event-scoped dimensions `hardware_model`, `game_name`, `game_id`, `execution_mode`, `thermal_state`, and the **sum** metrics `fps_measured_seconds`, `fps_frame_equivalents`, filtered to `game_performance`. All five dimensions must be registered. It computes FPS from numerator and duration instead of averaging per-event FPS. Pagination, schema and incomplete-data checks run before atomically replacing the public snapshot. Failed fetches preserve the last good publication. GitHub branch rules must allow the workflow to commit the aggregate JSON to `game-performance-dashboard`; otherwise that run fails and does not deploy a fresh claim. Daily data commits do not recursively trigger Actions because they use the workflow's `GITHUB_TOKEN`.

Daily refresh is prepared, **not verified operational until credentials are connected and a real API run succeeds**. Missing custom fields or Analytics processing delays can prevent updates. Check Actions and the page's reporting range and stale-data notice. This is a daily snapshot, not a live dashboard.

## Local preview and manual fallback

```sh
python3 -m http.server 8080 --directory docs
```

For a manual export, use the saved exploration with Hardware model / Game name / Game ID rows, Thermal state columns, and paired **FPS measured seconds / Average FPS** values. Export CSV with the selected dates, then run:

```sh
python3 scripts/import_analytics_csv.py /path/to/export.csv --mode jit
```

Select `--mode interpreter` only for an interpreter-filtered export. Seed data reconstructs frame equivalents from the unrounded exported weighted average × duration. Automatic API updates use the native numerator directly. Unobserved states stay absent, while an observed zero FPS remains a real stall.

```sh
python3 -m unittest discover -s tests -v
node tests/model.test.cjs
node --check docs/assets/app.js
```

The page offers text search, hardware and execution-mode filters, name/time/FPS sorting, filtered CSV export, a reporting date range and stale-data notice. FPS and duration describe observed running sessions, including loading and menus; they do not establish compatibility or comparable benchmark conditions.

## Branding

The header, favicon and touch icon use the exact `AppIcon-1024.png` from the RPCS3 Apple app asset catalog. The interface uses its violet/lavender palette in both light and dark appearances; the source icon is not recolored.

## Device names

`docs/assets/devices.js` maps Apple hardware identifiers to display names, checked against [DeviceKit](https://github.com/devicekit/DeviceKit/blob/master/Source/Device.generated.swift) and [AppleDB](https://appledb.dev/device-selection/iPhone) on 25 October 2026. It covers every code in the seed snapshot plus other supported iPhone/iPad models. Table cells expose original identifiers on hover; CSV export includes both names and codes. Search accepts either. The hardware filter combines Wi-Fi/cellular codes with the same model name without modifying the underlying measurements. The hardware summary counts distinct display models; the original seed contains 24 codes but 23 named models. Unknown future identifiers remain readable as their original codes.
