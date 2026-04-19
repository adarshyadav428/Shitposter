from __future__ import annotations

# ruff: noqa: E501


def render_dashboard_html() -> str:
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>News Ops Console</title>
  <style>
    :root {
      --bg-1: #0d1b1e;
      --bg-2: #15333a;
      --panel: rgba(8, 19, 22, 0.82);
      --text: #f2f2ea;
      --muted: #b7c4bf;
      --ok: #55d68b;
      --warn: #ffc857;
      --bad: #ff6b6b;
      --accent: #57c7ff;
      --ring: rgba(87, 199, 255, 0.28);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: \"Space Grotesk\", \"Segoe UI\", sans-serif;
      background:
        radial-gradient(1200px 480px at -10% -10%, #2b7a78 0%, transparent 48%),
        radial-gradient(900px 500px at 110% -15%, #ffb703 0%, transparent 42%),
        linear-gradient(180deg, var(--bg-2), var(--bg-1));
      padding: 24px;
    }

    .wrap {
      max-width: 1200px;
      margin: 0 auto;
      display: grid;
      gap: 16px;
    }

    .hero {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      padding: 18px 20px;
      border-radius: 16px;
      background: var(--panel);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }

    h1 {
      margin: 0;
      font-size: clamp(1.4rem, 2.2vw, 2rem);
      letter-spacing: 0.02em;
    }

    .subtitle {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 0.95rem;
    }

    .pulse {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: var(--warn);
      box-shadow: 0 0 0 0 rgba(255, 200, 87, 0.7);
      animation: pulse 1.8s infinite;
    }

    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(255, 200, 87, 0.7); }
      70% { box-shadow: 0 0 0 12px rgba(255, 200, 87, 0); }
      100% { box-shadow: 0 0 0 0 rgba(255, 200, 87, 0); }
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 14px;
    }

    .card {
      background: var(--panel);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 14px;
      padding: 14px;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
      transition: transform 120ms ease;
    }

    .card:hover {
      transform: translateY(-2px);
    }

    .card h2 {
      margin: 0 0 10px;
      font-size: 1rem;
      color: var(--muted);
      font-weight: 600;
      letter-spacing: 0.02em;
    }

    .metric-value {
      font-size: 1.9rem;
      line-height: 1.1;
      font-weight: 700;
    }

    .metric-note {
      margin-top: 6px;
      color: var(--muted);
      font-size: 0.88rem;
    }

    .span-3 { grid-column: span 3; }
    .span-4 { grid-column: span 4; }
    .span-6 { grid-column: span 6; }
    .span-8 { grid-column: span 8; }
    .span-12 { grid-column: span 12; }

    .status-ok { color: var(--ok); }
    .status-warn { color: var(--warn); }
    .status-bad { color: var(--bad); }

    .list {
      display: grid;
      gap: 8px;
      max-height: 360px;
      overflow: auto;
      padding-right: 4px;
    }

    .row {
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px;
      padding: 10px;
      background: rgba(255, 255, 255, 0.03);
    }

    .row-top {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-size: 0.92rem;
      margin-bottom: 4px;
    }

    .tag {
      display: inline-flex;
      border: 1px solid rgba(87, 199, 255, 0.45);
      color: var(--accent);
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 0.78rem;
      background: rgba(87, 199, 255, 0.08);
    }

    .mini-grid {
      display: grid;
      gap: 6px;
      grid-template-columns: 1fr 1fr;
    }

    .mini {
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 8px;
      background: rgba(255, 255, 255, 0.03);
      font-size: 0.9rem;
    }

    .k { color: var(--muted); }

    button {
      border: 1px solid var(--ring);
      border-radius: 10px;
      background: rgba(87, 199, 255, 0.14);
      color: var(--text);
      padding: 8px 12px;
      font-weight: 600;
      cursor: pointer;
    }

    button:hover {
      background: rgba(87, 199, 255, 0.24);
    }

    @media (max-width: 980px) {
      .span-3, .span-4, .span-6, .span-8 { grid-column: span 12; }
      body { padding: 14px; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <div>
        <h1>Autonomous News Ops Console</h1>
        <p class=\"subtitle\">Live monitor for ingest, verify, publish, and durability</p>
      </div>
      <div class=\"pulse\">
        <span class=\"dot\" id=\"live-dot\"></span>
        <span id=\"last-refresh\">Loading...</span>
        <button id=\"refresh-btn\" type=\"button\">Refresh Now</button>
      </div>
    </section>

    <section class=\"grid\">
      <article class=\"card span-3\">
        <h2>Autopilot</h2>
        <div class=\"metric-value\" id=\"autopilot-state\">-</div>
        <div class=\"metric-note\" id=\"autopilot-note\">-</div>
      </article>
      <article class=\"card span-3\">
        <h2>Events</h2>
        <div class=\"metric-value\" id=\"events-count\">0</div>
        <div class=\"metric-note\">Tracked canonical events</div>
      </article>
      <article class=\"card span-3\">
        <h2>Publications</h2>
        <div class=\"metric-value\" id=\"pub-count\">0</div>
        <div class=\"metric-note\" id=\"failed-pub\">Failed: 0</div>
      </article>
      <article class=\"card span-3\">
        <h2>Readiness</h2>
        <div class=\"metric-value\" id=\"readiness-state\">-</div>
        <div class=\"metric-note\" id=\"readiness-summary\">-</div>
      </article>

      <article class=\"card span-8\">
        <h2>Latest Events</h2>
        <div class=\"list\" id=\"events-list\"></div>
      </article>

      <article class=\"card span-4\">
        <h2>Drop Reasons</h2>
        <div class=\"list\" id=\"drops-list\"></div>
      </article>

      <article class=\"card span-6\">
        <h2>Channels</h2>
        <div class=\"mini-grid\" id=\"channels-grid\"></div>
      </article>

      <article class=\"card span-6\">
        <h2>Persistence</h2>
        <div class=\"mini-grid\" id=\"persistence-grid\"></div>
      </article>
    </section>
  </div>

  <script>
    async function getJson(path) {
      const res = await fetch(path, { cache: \"no-store\" });
      if (!res.ok) throw new Error(path + \" -> \" + res.status);
      return res.json();
    }

    function setText(id, value) {
      const el = document.getElementById(id);
      if (el) el.textContent = String(value);
    }

    function classifyBool(v) {
      if (v) return \"status-ok\";
      return \"status-bad\";
    }

    function renderEvents(events) {
      const root = document.getElementById(\"events-list\");
      root.innerHTML = \"\";
      if (!events.length) {
        root.innerHTML = '<div class=\"row\">No events yet.</div>';
        return;
      }
      for (const item of events) {
        const node = document.createElement(\"article\");
        node.className = \"row\";
        node.innerHTML =
          '<div class=\"row-top\"><strong>' + item.headline + '</strong><span class=\"tag\">' + item.sector + '</span></div>' +
          '<div class=\"k\">event_id: ' + item.event_id + '</div>' +
          '<div class=\"k\">witnesses: ' + item.witnesses + ' | updated: ' + item.updated_at + '</div>';
        root.appendChild(node);
      }
    }

    function renderDrops(dropReasons) {
      const root = document.getElementById(\"drops-list\");
      root.innerHTML = \"\";
      const entries = Object.entries(dropReasons || {});
      if (!entries.length) {
        root.innerHTML = '<div class=\"row\">No drops recorded.</div>';
        return;
      }
      entries.sort((a, b) => b[1] - a[1]);
      for (const [reason, count] of entries) {
        const node = document.createElement(\"div\");
        node.className = \"mini\";
        node.innerHTML = '<div><strong>' + reason + '</strong></div><div class=\"k\">count: ' + count + '</div>';
        root.appendChild(node);
      }
    }

    function renderChannels(channels) {
      const root = document.getElementById(\"channels-grid\");
      root.innerHTML = \"\";
      for (const row of channels) {
        const node = document.createElement(\"div\");
        node.className = \"mini\";
        const state = row.operational ? \"operational\" : \"not-ready\";
        node.innerHTML =
          '<div><strong>' + row.name + '</strong></div>' +
          '<div class=\"k\">enabled: ' + row.enabled + ' | mode: ' + row.mode + '</div>' +
          '<div class=\"' + (row.operational ? 'status-ok' : 'status-warn') + '\">' + state + '</div>';
        root.appendChild(node);
      }
    }

    function renderPersistence(persistence) {
      const root = document.getElementById(\"persistence-grid\");
      root.innerHTML = \"\";
      const rows = [
        [\"backend\", persistence.backend],
        [\"path\", persistence.path],
        [\"snapshot_enabled\", persistence.snapshot_enabled],
        [\"directory_exists\", persistence.directory_exists],
      ];
      for (const [k, v] of rows) {
        const node = document.createElement(\"div\");
        node.className = \"mini\";
        node.innerHTML = '<div><strong>' + k + '</strong></div><div class=\"k\">' + v + '</div>';
        root.appendChild(node);
      }
    }

    async function refresh() {
      try {
        const [stats, events, readiness] = await Promise.all([
          getJson(\"/stats\"),
          getJson(\"/events?limit=10\"),
          getJson(\"/system/readiness\"),
        ]);

        const running = Boolean(stats.autopilot && stats.autopilot.running);
        setText(\"autopilot-state\", running ? \"RUNNING\" : \"STOPPED\");
        setText(\"autopilot-note\", \"poll interval: \" + (stats.autopilot?.poll_interval_seconds ?? \"-\") + \"s\");
        document.getElementById(\"autopilot-state\").className = \"metric-value \" + classifyBool(running);

        setText(\"events-count\", stats.events ?? 0);
        setText(\"pub-count\", stats.publications ?? 0);
        setText(\"failed-pub\", \"Failed: \" + (stats.failed_publications ?? 0));

        const ready = Boolean(readiness.ready);
        setText(\"readiness-state\", ready ? \"READY\" : \"DEGRADED\");
        document.getElementById(\"readiness-state\").className = \"metric-value \" + (ready ? \"status-ok\" : \"status-warn\");
        setText(\"readiness-summary\", readiness.summary || \"\");

        renderEvents(events || []);
        renderDrops(stats.drop_reasons || {});
        renderChannels(readiness.channels || []);
        renderPersistence(readiness.persistence || {});

        setText(\"last-refresh\", \"Last refresh: \" + new Date().toLocaleTimeString());
      } catch (err) {
        setText(\"last-refresh\", \"Refresh failed: \" + err.message);
        document.getElementById(\"live-dot\").style.background = \"var(--bad)\";
      }
    }

    document.getElementById(\"refresh-btn\").addEventListener(\"click\", refresh);
    refresh();
    setInterval(refresh, 8000);
  </script>
</body>
</html>
"""
