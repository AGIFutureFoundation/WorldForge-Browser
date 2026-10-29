<!doctype html>
<html lang="en">
  <head>
    <link rel="preconnect" href="https://clerk.kylon.io" crossorigin="anonymous" />
    <link rel="preconnect" href="https://clerk.kylon.io" />
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
    <meta name="theme-color" content="#FFFFFF" />
    <meta name="description" content="Team operations in Kylon" />
    <meta property="og:site_name" content="Kylon" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="Kylon" />
    <meta property="og:description" content="Team operations in Kylon" />
    <meta property="og:image" content="https://app.kylon.io/og/kylon-resource-v2.png?v=20261013" />
    <meta property="og:image:type" content="image/png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="Kylon - Your first company harness. Where humans and agents run your business together" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="Kylon" />
    <meta name="twitter:description" content="Team operations in Kylon" />
    <meta name="twitter:image" content="https://app.kylon.io/og/kylon-resource-v2.png?v=20261013" />
    <meta name="twitter:image:alt" content="Kylon - Your first company harness. Where humans and agents run your business together" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" data-favicon-badge />
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
    <link rel="apple-touch-icon" sizes="512x512" href="/apple-touch-icon.png" />
    <link rel="manifest" href="/manifest.json" />
    <title>Kylon</title>
    <style>
      /* Pre-React boot skeleton for workspace routes. Injected by the body
         script below, then released by the first committed React tree before
         the browser paints it.

         It is a pixel mirror of the shape-only skeletons in
         timeline-sidebar-skeleton.tsx and chat-sidebar-skeleton.tsx: same chrome stubs (title bar, filter
         pills), same row geometry, same pulse timing as Tailwind's
         animate-pulse, colors mirroring app.css tokens for both themes.
         Shapes only — no text, no interactive lookalikes. That keeps the
         skeleton visually continuous across every boot stage — pre-React,
         auth gate, /sidebar fetch, timeline query — so the sidebar reads as
         loading exactly once. Geometry, copy, and colors are pinned against
         the app sources by boot-skeleton-parity.test.ts. */
      #kylon-app-root[data-boot-skeleton] {
        --boot-surface: #ffffff;
        position: fixed;
        inset: 0;
        display: flex;
        background: #ffffff;
      }
      #kylon-app-root[data-boot-skeleton].boot-dark {
        --boot-surface: #221d17;
        background: #221d17;
      }
      [data-boot-skeleton] * {
        box-sizing: border-box;
      }
      [data-boot-skeleton] .boot-rail,
      [data-boot-skeleton] .boot-side {
        background: var(--boot-surface);
      }
      [data-boot-skeleton] .boot-rail {
        width: 52px;
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        border-right: 0.5px solid rgba(58, 37, 25, 0.096);
      }
      /* Fixed rail entries mirror workspace-icon-rail.tsx, including the
         Search/Chat/Members and Connections above the account avatar. */
      [data-boot-skeleton] .boot-rail-logo-zone {
        display: flex;
        height: 60px;
        width: 100%;
        flex-shrink: 0;
        align-items: center;
        justify-content: center;
        padding: 0 6px;
      }
      [data-boot-skeleton] .boot-rail-logo {
        width: 40px;
        height: 40px;
        border-radius: 8px;
      }
      [data-boot-skeleton] .boot-rail-nav {
        display: flex;
        min-height: 0;
        flex: 1;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 0 6px;
      }
      [data-boot-skeleton] .boot-rail-btn {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        flex-shrink: 0;
      }
      [data-boot-skeleton] .boot-rail-bottom {
        margin-top: auto;
        display: flex;
        width: 100%;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        padding: 12px 6px;
      }
      [data-boot-skeleton] .boot-rail-bottom .boot-rail-btn {
        width: 32px;
        height: 32px;
        border-radius: 8px;
      }
      [data-boot-skeleton] .boot-rail-utilities {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
      }
      [data-boot-skeleton] .boot-rail-avatar {
        width: 32px;
        height: 32px;
        border-radius: 9999px;
      }
      [data-boot-skeleton] .boot-side {
        position: relative;
        width: 390px;
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border-right: 0.5px solid rgba(58, 37, 25, 0.096);
      }
      /* The default variant may settle into a layout with no sidebar at
         all (settings, billing), so it draws no column border. */
      [data-boot-skeleton] .boot-side-plain {
        border-right: 0;
      }
      /* Mirrors the Apps directory frame (app-directory-skeleton.tsx): Settings'
         gutters, a centered 1152px (max-w-6xl) column, and 15rem auto-fill tracks. */
      [data-boot-skeleton] .boot-apps { min-width: 0; flex: 1; overflow: hidden; padding: 24px 16px; }
      [data-boot-skeleton] .boot-apps-column { max-width: 1152px; margin: 0 auto; }
      [data-boot-skeleton] .boot-apps-title { height: 24px; display: flex; align-items: center; margin-bottom: 24px; }
      [data-boot-skeleton] .boot-apps-search { height: 36px; width: 100%; max-width: 448px; margin-bottom: 24px; border-radius: 12px; }
      [data-boot-skeleton] .boot-apps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 24px; }
      [data-boot-skeleton] .boot-apps-card { min-width: 0; overflow: hidden; border: 0.5px solid rgba(58,37,25,0.113); border-radius: 16px; background: rgba(244,236,221,0.5); }
      [data-boot-skeleton].boot-dark .boot-apps-card { border-color: rgba(244,237,226,0.113); background: rgba(44,38,30,0.3); }
      [data-boot-skeleton] .boot-apps-preview { width: 100%; aspect-ratio: 16 / 9; }
      [data-boot-skeleton] .boot-apps-footer { display: flex; height: 48px; align-items: center; gap: 8px; padding: 8px 12px; }
      [data-boot-skeleton] .boot-apps-lines { min-width: 0; flex: 1; }
      [data-boot-skeleton] .boot-apps-action { display: flex; width: 32px; height: 32px; flex-shrink: 0; align-items: center; justify-content: center; }
      [data-boot-skeleton] .boot-app-frame { display: flex; min-width: 0; flex: 1; flex-direction: column; overflow: hidden; }
      [data-boot-skeleton] .boot-app-header { display: grid; height: 48px; flex-shrink: 0; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 0 12px; }
      [data-boot-skeleton] .boot-app-body { flex: 1; display: flex; flex-direction: column; gap: 8px; padding: 16px; }
      [data-boot-skeleton] .boot-app-stub { border-radius: 12px; flex-shrink: 0; }
      @media (min-width: 640px) { [data-boot-skeleton] .boot-apps { padding: 24px 20px; } }
      @media (min-width: 1024px) { [data-boot-skeleton] .boot-apps { padding: 24px; } }
      @media (prefers-reduced-motion: reduce) { [data-boot-skeleton] .boot-apps .boot-skel, [data-boot-skeleton] .boot-app-frame .boot-skel { animation: none; } }
      [data-boot-skeleton] .boot-main {
        flex: 1;
      }
      [data-boot-skeleton] .boot-title-row {
        display: flex;
        min-width: 0;
        padding: 16px 64px 0 20px;
      }
      [data-boot-skeleton] .boot-pills {
        display: flex;
        align-items: center;
        gap: 2px;
        padding: 16px 16px 16px 20px;
      }
      /* Pill-shaped stubs standing in for the filter pills; widths
         approximate Home / Recent / Unread / @me so the row footprint
         holds steady (mirrors CHAT_FILTER_PILL_STUB_WIDTHS). */
      [data-boot-skeleton] .boot-pill-stub {
        height: 32px;
        flex-shrink: 0;
        border-radius: 9999px;
      }
      /* Chat mirrors chat-sidebar-skeleton.tsx: 60px rows, 36px avatar,
         two text lines in 20px/16px slots, and borderless 36px group headers. */
      [data-boot-skeleton] .boot-chat-item {
        display: flex; height: 60px; align-items: center; gap: 12px; padding: 10px 16px 10px 21px;
      }
      [data-boot-skeleton] .boot-chat-lines { min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 4px; }
      [data-boot-skeleton] .boot-chat-title { display: flex; height: 20px; align-items: center; }
      [data-boot-skeleton] .boot-chat-description { display: flex; height: 16px; align-items: center; }
      [data-boot-skeleton] .boot-chat-title .boot-line { width: 66.666667%; }
      [data-boot-skeleton] .boot-chat-description .boot-line { width: 100%; }
      [data-boot-skeleton] .boot-chat-group { display: flex; height: 36px; align-items: center; gap: 6px; padding: 0 16px 0 32px; }
      [data-boot-skeleton] .boot-chat-group-rows { padding-bottom: 8px; }
      [data-boot-skeleton] .boot-chat-lobby { padding-bottom: 16px; }
      [data-boot-skeleton] .boot-avatar {
        width: 36px;
        height: 36px;
        flex-shrink: 0;
        border-radius: 9999px;
      }
      [data-boot-skeleton] .boot-line {
        height: 12px;
        border-radius: 4px;
      }
      /* A Chat group header's stubs (18px circle + w-28 line), mirroring
         ChatRoomPlaceholder. No interactive lookalikes. */
      [data-boot-skeleton] .boot-ch-dot {
        width: 18px;
        height: 18px;
        flex-shrink: 0;
        border-radius: 9999px;
      }
      [data-boot-skeleton] .boot-ch-line {
        height: 12px;
        width: 112px;
        border-radius: 4px;
      }
      /* Default variant for other workspace routes: a title-shaped bar in
         the standard title position, no list shape commitment (mirrors
         DefaultSidebarSkeleton). */
      [data-boot-skeleton] .boot-title-stub-row {
        display: flex;
        height: 32px;
        align-items: center;
      }
      [data-boot-skeleton] .boot-title-stub {
        height: 16px;
        width: 96px;
        border-radius: 4px;
      }
      [data-boot-skeleton] .boot-title-stub-feed {
        width: 48px;
      }
      /* Mirrors Tailwind animate-pulse (2s, same easing, 1 -> 0.5 -> 1).
         Both boot and React shapes anchor to the document timeline. */
      [data-boot-skeleton] .boot-skel {
        background: rgba(27, 23, 18, 0.04);
        animation: kylon-boot-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
      }
      [data-boot-skeleton].boot-dark .boot-rail,
      [data-boot-skeleton].boot-dark .boot-side {
        border-color: rgba(244, 237, 226, 0.096);
      }
      [data-boot-skeleton].boot-dark .boot-skel {
        background: rgba(244, 237, 226, 0.12);
      }
      @keyframes kylon-boot-pulse {
        0%,
        100% {
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        [data-boot-skeleton] .boot-skel {
          animation: none;
        }
      }
      /* macOS desktop shell (same selector as the desktop-darwin variant in
         app.css): the rail widens to 68px around the traffic lights and
         reserves the 16px drag strip, as workspace-icon-rail.tsx does. */
      html[data-desktop-shell="darwin"]:not([data-desktop-fullscreen]) [data-boot-skeleton] .boot-rail {
        width: 68px;
      }
      html[data-desktop-shell="darwin"]:not([data-desktop-fullscreen]) [data-boot-skeleton] .boot-rail::before {
        content: "";
        height: 16px;
        flex-shrink: 0;
        -webkit-app-region: drag;
      }
      html[data-desktop-shell="darwin"]:not([data-desktop-fullscreen]) [data-boot-skeleton] .boot-rail-logo-zone {
        -webkit-app-region: drag;
      }
      /* Mirror the app's mobile boundary (use-mobile.ts MOBILE_BREAKPOINT). */
      @media (max-width: 1023px) {
        [data-boot-skeleton] .boot-rail,
        [data-boot-skeleton] .boot-side {
          display: none;
        }
      }
    </style>
    <script>
      // Desktop-shell markers before first paint. The preload bridge exists
      // before any page script runs, but main.tsx's installDesktopShellMarker
      // only runs once the entry chunk loads — too late for the static boot
      // skeleton below. Same predicate as getDesktopBridge (desktop.ts). The
      // fullscreen marker covers a page loaded while the window is already
      // fullscreen (a reload, an update refresh), which gets no change event;
      // Subscribe now as well: fullscreen may change while the entry downloads.
      // installDesktopShellMarker takes over this listener once the entry runs.
      (function () {
        var bridge = window.p2Desktop;
        if (bridge && bridge.shell === "electron" && typeof bridge.platform === "string") {
          document.documentElement.setAttribute("data-desktop-shell", bridge.platform);
          function markFullScreen(fullScreen) {
            if (fullScreen === true) document.documentElement.setAttribute("data-desktop-fullscreen", "");
            else document.documentElement.removeAttribute("data-desktop-fullscreen");
          }
          if (typeof bridge.isFullScreen === "function") markFullScreen(bridge.isFullScreen());
          if (typeof bridge.onFullScreenChange === "function") {
            window.__p2BootDesktopCleanup = bridge.onFullScreenChange(markFullScreen);
          }
        }
      })();
    </script>
    <script>
      // Preconnect to the cross-origin hosts the app hits immediately after
      // boot: the API, the SSE endpoint, and Clerk's frontend API (derived
      // from the publishable key, which base64-encodes its domain). Vite
      // replaces %VITE_*% at build time; unset vars keep the literal and are
      // filtered by the percent guard. Same-origin values (proxy setups) are
      // skipped. API/SSE requests carry a Bearer header without cookies, so
      // they use the anonymous connection pool (crossorigin); Clerk loads a
      // classic script and cookied requests, so it preconnects credentialed.
      (function () {
        function add(origin, anonymous) {
          if (!origin || origin.indexOf("%") !== -1) return;
          try {
            var url = new URL(origin, window.location.href);
            if (url.origin === window.location.origin) return;
            var link = document.createElement("link");
            link.rel = "preconnect";
            link.href = url.origin;
            if (anonymous) link.crossOrigin = "anonymous";
            document.head.appendChild(link);
          } catch (_e) {
            // Malformed configured origin — skip the hint.
          }
        }
        add("https://api.kylon.io", true);
        add("https://api.kylon.io", true);
        var clerkKey = "pk_live_Y2xlcmsua3lsb24uaW8k";
        if (clerkKey && clerkKey.indexOf("%") === -1) {
          var encodedDomain = clerkKey.split("_").pop();
          try {
            add("https://" + atob(encodedDomain).replace(/\$$/, ""), false);
          } catch (_e) {
            // Unexpected key shape — skip the hint.
          }
        }
      })();
    </script>
    <script>
      // Environment-specific favicon and title before the app mounts.
      // VITE_DEPLOY_ENV drives the favicon: "development" → dark variant.
      // VITE_APP_VARIANT drives the title: "preview" → PR number/title.
      // Vite replaces %VITE_*% at build time; unset vars keep the literal.
      (function () {
        var variant = "%VITE_APP_VARIANT%";
        var deployEnv = "production";

        if (deployEnv === "development") {
          var svgLink = document.querySelector('link[rel="icon"][type="image/svg+xml"]');
          if (svgLink) svgLink.setAttribute("href", "/favicon-dev.svg");
          // Remove raster fallbacks (ico/png) so the browser uses the SVG.
          // Without this, some browsers prefer the ico over the svg and show
          // the wrong (production green) favicon.
          var fallbacks = document.querySelectorAll(
            'link[rel="icon"]:not([data-favicon-badge])'
          );
          for (var j = 0; j < fallbacks.length; j++) fallbacks[j].remove();
          var manifestLink = document.querySelector('link[rel="manifest"]');
          if (manifestLink) manifestLink.setAttribute("href", "/manifest-dev.json");
        }

        if (variant === "preview") {
          var previewConfig = window.__P2_PREVIEW_CONFIG__ || {};
          var previewPrNumberRaw = previewConfig.prNumber || "%VITE_PREVIEW_PR_NUMBER%";
          var previewPrTitleRaw = previewConfig.prTitle || "%VITE_PREVIEW_PR_TITLE%";
          var prNumber = /^[0-9]+$/.test(previewPrNumberRaw) ? previewPrNumberRaw : null;
          var prTitle = null;
          if (previewPrTitleRaw && previewPrTitleRaw !== "%VITE_PREVIEW_PR_TITLE%") {
            var decoded = previewConfig.prTitle;
            if (typeof decoded !== "string") {
              try {
                decoded = decodeURIComponent(previewPrTitleRaw);
              } catch (_e) {
                decoded = null;
              }
            }
            if (decoded) {
              decoded = decoded.trim();
              if (decoded.length > 0) prTitle = decoded;
            }
          }
          var title;
          if (prNumber && prTitle) title = "Kylon (PR #" + prNumber + ": " + prTitle + ")";
          else if (prNumber) title = "Kylon (PR #" + prNumber + ")";
          else if (prTitle) title = "Kylon (PRE: " + prTitle + ")";
          else title = "Kylon (PRE)";
          document.title = title;
        } else if (deployEnv === "development") {
          document.title = "Kylon (DEV)";
        }
      })();
    </script>
    <link rel="modulepreload" crossorigin data-kylon-entry href="/assets/index-DWP9T_qN.js">
    <noscript data-kylon-entry-compat><script type="module" crossorigin src="/assets/index-DWP9T_qN.js"></script></noscript>
    <script>
      (function () {
        var ENTRY = "/assets/index-DWP9T_qN.js";
        var RECOVERY_KEY = "__kylon_entry_recovery";
        var RELOAD_MARKER_PARAM = "__kylon_entry_reload";
        var LOAD_FAILURE_RE = /failed to fetch dynamically imported module|error loading dynamically imported module|importing a module script failed|failed to load module script/i;

        function isLoadFailure(error) {
          var message = error && error.message ? error.message : String(error);
          return LOAD_FAILURE_RE.test(String(message));
        }

        function writeSession(key, value) {
          try { window.sessionStorage.setItem(key, value); } catch (error) {}
        }

        function hasReloadMarker() {
          // Fail closed: when the URL cannot be inspected, assume the reload
          // already happened so the ladder can never loop.
          try { return new URL(window.location.href).searchParams.has(RELOAD_MARKER_PARAM); } catch (error) { return true; }
        }

        function tryNavigateWithReloadMarker() {
          try {
            var url = new URL(window.location.href);
            url.searchParams.set(RELOAD_MARKER_PARAM, String(Date.now()));
            window.location.replace(url.href);
            return true;
          } catch (error) {
            return false;
          }
        }

        function removeReloadMarkerFromUrl() {
          try {
            var url = new URL(window.location.href);
            if (!url.searchParams.has(RELOAD_MARKER_PARAM)) return;
            url.searchParams.delete(RELOAD_MARKER_PARAM);
            window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
          } catch (error) {}
        }

        var domReady = document.readyState === "loading"
          ? new Promise(function (resolve) {
              document.addEventListener("DOMContentLoaded", function () { resolve(); }, { once: true });
            })
          : Promise.resolve();

        function importEntry(step) {
          var url = ENTRY;
          if (step === 1) url = ENTRY + "?kylon_retry=1";
          if (step === 2) url = ENTRY + "?kylon_retry=2." + Date.now();
          if (step > 0) {
            writeSession(RECOVERY_KEY, JSON.stringify({ step: step, at: Date.now() }));
          }
          return import(url).then(function (loadedModule) {
            removeReloadMarkerFromUrl();
            return loadedModule;
          });
        }

        function showFailureScreen() {
          var root = document.getElementById("kylon-app-root");
          if (!root) return;
          root.innerHTML =
            '<div style="display:flex;min-height:100vh;align-items:center;justify-content:center;font-family:system-ui,sans-serif;text-align:center;padding:32px">' +
            '<div><p style="font-size:15px;font-weight:600;margin:0 0 8px">Kylon failed to load</p>' +
            '<p style="font-size:13px;margin:0 0 16px">A network or caching problem is preventing the app from starting.</p>' +
            '<button id="kylon-entry-retry" style="font:inherit;font-size:13px;padding:6px 14px;cursor:pointer">Try again</button>' +
            '</div></div>';
          var retry = document.getElementById("kylon-entry-retry");
          if (retry) {
            retry.addEventListener("click", function () {
              // A human-initiated retry gets a full fresh cycle, including a
              // new automatic-reload allowance: navigate without the marker.
              try {
                var url = new URL(window.location.href);
                url.searchParams.delete(RELOAD_MARKER_PARAM);
                window.location.replace(url.href);
              } catch (error) {
                window.location.reload();
              }
            });
          }
        }

        domReady
          .then(function () { return importEntry(0); })
          .catch(function (primaryError) {
            if (!isLoadFailure(primaryError)) throw primaryError;
            console.warn("kylon-entry-bootstrap: entry failed, retrying under a stable cache key", primaryError);
            return importEntry(1).catch(function (stableRetryError) {
              if (!isLoadFailure(stableRetryError)) throw stableRetryError;
              console.warn("kylon-entry-bootstrap: stable retry failed, bypassing caches", stableRetryError);
              return importEntry(2).catch(function (bypassError) {
                if (!isLoadFailure(bypassError)) throw bypassError;
                if (!hasReloadMarker()) {
                  writeSession(RECOVERY_KEY, JSON.stringify({
                    step: "reload",
                    at: Date.now(),
                    message: String((bypassError && bypassError.message) || bypassError).slice(0, 300)
                  }));
                  if (tryNavigateWithReloadMarker()) return;
                }
                console.error("kylon-entry-bootstrap: all recovery attempts failed", bypassError);
                showFailureScreen();
              });
            });
          });
      })();
    </script>
    <link rel="stylesheet" crossorigin href="/assets/index-Bhoaqxiu.css">
  </head>
  <body>
    <div id="kylon-app-root"></div>
    <script>
      // Boot skeleton for workspace routes: structure on screen while the
      // entry chunk downloads and parses. React clears the markup on mount
      // (createRoot replaces container children); BootSkeletonHandoff removes
      // the attribute and theme class in that commit's layout phase.
      (function () {
        try {
          var root = document.getElementById("kylon-app-root");
          if (!root) return;
          var path = window.location.pathname;
          if (path !== "/" && path.indexOf("/workspaces/") !== 0) return;
          var stored = null;
          try {
            stored = window.localStorage.getItem("theme");
          } catch (_e) {
            // Storage may be blocked; fall through to the light default.
          }
          var dark =
            stored === "dark" ||
            (stored === "system" &&
              window.matchMedia &&
              window.matchMedia("(prefers-color-scheme: dark)").matches);
          root.setAttribute("data-boot-skeleton", "");
          if (dark) root.classList.add("boot-dark");
          // Variant selection mirrors workspaceBootSkeletonVariant /
          // workspaceRouteSidebarLayout (workspace-sidebar-layout.ts): every
          // route with a conversation sidebar gets the Chat shape, including
          // the Feed and Rooms addresses that redirect to it; other routes
          // retain their dedicated or neutral skeleton.
          // boot-skeleton-parity.test.ts runs both predicates over the same
          // sample paths.
          var rest = path === "/" ? "" : path.replace(/^\/workspaces\/[^/]+\/?/, "");
          var variant = "chat";
          if (rest === "apps" || rest === "apps/") {
            variant = "apps";
          } else if (/^private\/app\/[^/]+(?:\/|$)/.test(rest)) {
            variant = "app";
          } else if (
            rest === "settings" ||
            rest.indexOf("settings/") === 0 ||
            rest === "billing" ||
            rest === "connections" ||
            rest === "connections/" ||
            rest.indexOf("private/app/") === 0 ||
            rest.indexOf("private/url/") === 0 ||
            rest === "members" ||
            rest.indexOf("members/") === 0 ||
            rest === "knowledge" ||
            rest.indexOf("knowledge/") === 0 ||
            /^agent\/[^/]+\/(profile|members|connections|debug|skills|secrets|settings)\/*$/i.test(
              rest,
            )
          ) {
            variant = "default";
          }
          var side = "";
          if (variant === "chat") {
            var chatRow = '<div class="boot-chat-item"><div class="boot-avatar boot-skel"></div>' +
              '<div class="boot-chat-lines"><div class="boot-chat-title"><div class="boot-line boot-skel"></div></div>' +
              '<div class="boot-chat-description"><div class="boot-line boot-skel"></div></div></div></div>';
            var group = '<div class="boot-chat-group"><div class="boot-ch-dot boot-skel"></div><div class="boot-ch-line boot-skel"></div></div>';
            var chatParams = new URLSearchParams(window.location.search);
            var flatChatList = ["recents", "unread", "mentioned"].indexOf(chatParams.get("chat")) !== -1 ||
              ["all", "created_by_me", "unread", "mentioned"].indexOf(chatParams.get("timeline")) !== -1;
            var chatRows = "";
            if (flatChatList) {
              for (var cr = 0; cr < 8; cr++) chatRows += chatRow;
            } else {
              for (var cg = 0; cg < 2; cg++) {
                chatRows += group + '<div class="boot-chat-group-rows">';
                for (var ci = 0; ci < 5; ci++) chatRows += chatRow;
                chatRows += "</div>";
              }
              for (var gh = 0; gh < 12; gh++) chatRows += group;
              chatRows = '<div class="boot-chat-lobby">' + chatRows + '</div>';
            }
            side = '<div class="boot-title-row"><div class="boot-title-stub-row">' +
              '<div class="boot-title-stub boot-title-stub-feed boot-skel"></div></div></div>' +
              '<div class="boot-pills">' +
              '<span class="boot-pill-stub boot-skel" style="width:68px"></span>' +
              '<span class="boot-pill-stub boot-skel" style="width:80px"></span>' +
              '<span class="boot-pill-stub boot-skel" style="width:72px"></span>' +
              '<span class="boot-pill-stub boot-skel" style="width:56px"></span></div>' + chatRows;
          } else if (variant === "default") {
            side =
              '<div class="boot-title-row"><div class="boot-title-stub-row">' +
              '<div class="boot-title-stub boot-skel"></div>' +
              "</div></div>";
          }
          var railButtons = '';
          for (var r = 0; r < 3; r++) {
            railButtons += '<div class="boot-rail-btn boot-skel"></div>';
          }
          var rail =
            '<div class="boot-rail-logo-zone"><div class="boot-rail-logo boot-skel"></div></div>' +
            '<div class="boot-rail-nav">' + railButtons + "</div>" +
            '<div class="boot-rail-bottom"><div class="boot-rail-utilities"><div class="boot-rail-btn boot-skel"></div>' +
            '<div class="boot-rail-btn boot-skel"></div></div>' +
            '<div class="boot-rail-avatar boot-skel"></div></div>';
          function appStub(width, height) {
            return '<div class="boot-app-stub boot-skel" style="width:' + width + ';height:' + height + '"></div>';
          }
          var main = '';
          if (variant === "apps") {
            var cards = '';
            for (var a = 0; a < 12; a++) {
              cards += '<div class="boot-apps-card"><div class="boot-apps-preview boot-skel"></div>' +
                '<div class="boot-apps-footer">' + appStub('20px', '20px') +
                '<div class="boot-apps-lines">' + appStub('66.666667%', '12px') +
                '<div style="height:4px"></div>' + appStub('83.333333%', '10px') + '</div>' +
                '<div class="boot-apps-action">' + appStub('16px', '16px') + '</div></div></div>';
            }
            main = '<div class="boot-apps"><div class="boot-apps-column"><div class="boot-apps-title">' +
              appStub('80px', '24px') + '</div><div class="boot-apps-search boot-skel"></div>' +
              '<div class="boot-apps-grid">' + cards + '</div></div></div>';
          } else if (variant === "app") {
            main = '<div class="boot-app-frame"><div class="boot-app-header">' + appStub('96px', '14px') +
              appStub('176px', '14px') + '<div style="display:flex;justify-content:flex-end;gap:8px">' +
              appStub('56px', '14px') + appStub('14px', '14px') + '</div></div>' +
              '<div class="boot-app-body">' + appStub('160px', '14px') + appStub('256px', '14px') + '</div></div>';
          } else {
            main = '<div class="boot-side' + (variant === "default" ? " boot-side-plain" : "") + '">' + side + "</div>" + '<div class="boot-main"></div>';
          }
          root.innerHTML = '<div class="boot-rail">' + rail + '</div>' + main;
          root.querySelectorAll('.boot-skel').forEach(function (element) {
            (element.getAnimations ? element.getAnimations() : []).forEach(function (animation) {
              if (animation.animationName === 'kylon-boot-pulse') animation.startTime = 0;
            });
          });
        } catch (_e) {
          // Never let the skeleton break boot.
        }
      })();
    </script>
  </body>
</html>
