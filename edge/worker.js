/**
 * MediSys Edge Worker — Cloudflare Worker
 *
 * Routes:
 *   /health          → static JSON response (fast, no origin needed)
 *   /api/*           → proxies to BACKEND_ORIGIN
 *   /uploads/*       → proxies to BACKEND_ORIGIN (file storage)
 *   everything else  → proxies to BACKEND_ORIGIN
 *
 * Environment variables (set in Cloudflare dashboard or wrangler.toml):
 *   BACKEND_ORIGIN   URL of the backend server, e.g. https://api.medisys.example.com
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ── Fast static healthcheck (no origin round-trip) ──────────────
    if (url.pathname === "/edge-health") {
      return new Response(
        JSON.stringify({ status: "ok", edge: true, timestamp: Date.now() }),
        {
          headers: {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "X-Served-By": "cloudflare-edge",
          },
        }
      );
    }

    // ── Route to backend origin ──────────────────────────────────────
    const origin = env.BACKEND_ORIGIN;
    if (!origin) {
      return new Response(
        JSON.stringify({ error: "BACKEND_ORIGIN not configured" }),
        { status: 503, headers: { "Content-Type": "application/json" } }
      );
    }

    const targetUrl = new URL(url.pathname + url.search, origin);
    const proxyRequest = new Request(targetUrl.toString(), {
      method: request.method,
      headers: request.headers,
      body: ["GET", "HEAD"].includes(request.method) ? null : request.body,
      redirect: "follow",
    });

    // Add forwarding headers
    const forwarded = new Headers(proxyRequest.headers);
    forwarded.set("X-Forwarded-For", request.headers.get("CF-Connecting-IP") || "");
    forwarded.set("X-Real-IP", request.headers.get("CF-Connecting-IP") || "");
    forwarded.set("X-Forwarded-Proto", "https");
    forwarded.set("X-Forwarded-Host", url.hostname);

    try {
      const response = await fetch(
        new Request(targetUrl.toString(), {
          method: request.method,
          headers: forwarded,
          body: ["GET", "HEAD"].includes(request.method) ? null : request.body,
        })
      );

      const responseHeaders = new Headers(response.headers);
      responseHeaders.set("X-Served-By", "medisys-edge");
      responseHeaders.set("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
      responseHeaders.set("X-Frame-Options", "SAMEORIGIN");
      responseHeaders.set("X-Content-Type-Options", "nosniff");
      responseHeaders.set("Referrer-Policy", "strict-origin-when-cross-origin");

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    } catch (err) {
      return new Response(
        JSON.stringify({ error: "Backend unreachable", detail: err.message }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  },
};
