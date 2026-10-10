/**
 * Cloudflare Pages Function: POST /api/lead
 * Forwards contact form submissions to Make via MAKE_WEBHOOK_URL.
 * Set the secret in Cloudflare Pages: MAKE_WEBHOOK_URL
 */
const CONTACT_EMAIL = "willynoslo17@gmail.com";

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...extraHeaders,
    },
  });
}

function corsHeaders(request) {
  const origin = request.headers.get("Origin") || "";
  const allowed =
    !origin ||
    origin.endsWith("mlinternasjonal.no") ||
    origin.includes("localhost") ||
    origin.includes("pages.dev");
  return {
    "Access-Control-Allow-Origin": allowed ? origin || "*" : "https://mlinternasjonal.no",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    Vary: "Origin",
  };
}

export async function onRequestOptions(context) {
  return new Response(null, { status: 204, headers: corsHeaders(context.request) });
}

export async function onRequestPost(context) {
  const headers = corsHeaders(context.request);

  try {
    const contentType = context.request.headers.get("Content-Type") || "";
    if (!contentType.includes("application/json")) {
      return json(
        { ok: false, error: "invalid_content_type", contactEmail: CONTACT_EMAIL },
        400,
        headers
      );
    }

    const body = await context.request.json();
    const name = String(body.name || "").trim();
    const email = String(body.email || "").trim();
    const message = String(body.message || "").trim();
    const lang = String(body.lang || "no").trim();
    const company = String(body.company || "").trim();
    const website = String(body.website || "").trim(); // honeypot

    if (website) {
      return json({ ok: true }, 200, headers);
    }

    if (!name || !email || !message) {
      return json(
        { ok: false, error: "missing_fields", contactEmail: CONTACT_EMAIL },
        400,
        headers
      );
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return json(
        { ok: false, error: "invalid_email", contactEmail: CONTACT_EMAIL },
        400,
        headers
      );
    }

    const interest = String(body.interest || "").trim();

    const payload = {
      source: "mlinternasjonal.no",
      name,
      email,
      company,
      interest,
      message,
      lang,
      submittedAt: new Date().toISOString(),
    };

    const webhookUrl = context.env.MAKE_WEBHOOK_URL;
    if (!webhookUrl) {
      // No webhook configured: surface the contact email to the client (still HTTP 200).
      return json(
        { ok: false, error: "webhook_not_configured", contactEmail: CONTACT_EMAIL },
        200,
        headers
      );
    }

    const upstream = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!upstream.ok) {
      return json(
        { ok: false, error: "upstream_failed", contactEmail: CONTACT_EMAIL },
        502,
        headers
      );
    }

    return json({ ok: true }, 200, headers);
  } catch (err) {
    return json(
      { ok: false, error: "server_error", contactEmail: CONTACT_EMAIL },
      500,
      headers
    );
  }
}

export async function onRequestGet() {
  return json({ ok: false, error: "method_not_allowed", contactEmail: CONTACT_EMAIL }, 405);
}
