/**
 * Cloudflare Pages Function: POST /api/lead
 * Delivers contact form submissions to info@mlinternasjonal.no
 * via the EMAIL send_email binding (Cloudflare Email Routing).
 * Optional: also POST to MAKE_WEBHOOK_URL if that Pages secret is set.
 */
const CONTACT_EMAIL = "info@mlinternasjonal.no";
const FROM_EMAIL = "skjema@mlinternasjonal.no";

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

function oneLine(value) {
  return String(value || "").replace(/[\r\n]+/g, " ").trim();
}

function b64utf8(value) {
  const bytes = new TextEncoder().encode(value);
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

function encodeHeader(value) {
  const clean = oneLine(value);
  if (/^[\x20-\x7E]*$/.test(clean)) return clean;
  return "=?UTF-8?B?" + b64utf8(clean) + "?=";
}

function buildMime({ from, to, replyTo, subject, text }) {
  const mid = "<" + crypto.randomUUID() + "@mlinternasjonal.no>";
  return [
    "From: ML Internasjonal Handel <" + from + ">",
    "To: " + to,
    "Reply-To: " + replyTo,
    "Subject: " + encodeHeader(subject),
    "Message-ID: " + mid,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: 8bit",
    "",
    text,
  ].join("\r\n");
}

function letter(payload) {
  return [
    "Ny henvendelse fra mlinternasjonal.no",
    "",
    "Navn: " + payload.name,
    "E-post: " + payload.email,
    "Firma: " + (payload.company || "—"),
    "Type: " + payload.interest,
    "Språk: " + payload.lang,
    "Tid: " + payload.submittedAt,
    "",
    "Melding:",
    payload.message,
  ].join("\n");
}

async function deliverEmail(env, payload) {
  if (!env.EMAIL || typeof env.EMAIL.send !== "function") {
    throw new Error("email_binding_missing");
  }
  const to = env.CONTACT_INBOX || "willynoslo17@gmail.com";
  const subject = "Henvendelse fra nettsiden (" + oneLine(payload.interest) + ") — " + oneLine(payload.name);
  const text = letter(payload);

  try {
    await env.EMAIL.send({
      to,
      from: { email: FROM_EMAIL, name: "ML Internasjonal Handel" },
      replyTo: payload.email,
      subject,
      text,
    });
    return;
  } catch (structuredErr) {
    const { EmailMessage } = await import("cloudflare:email");
    const raw = buildMime({
      from: FROM_EMAIL,
      to,
      replyTo: payload.email,
      subject,
      text,
    });
    await env.EMAIL.send(new EmailMessage(FROM_EMAIL, to, raw));
  }
}

async function notifyWebhook(env, payload) {
  const webhookUrl = env.MAKE_WEBHOOK_URL;
  if (!webhookUrl) return;
  const upstream = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!upstream.ok) {
    console.error("webhook_failed", upstream.status);
  }
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
    const interest = String(body.interest || "").trim();

    if (website) {
      return json({ ok: true }, 200, headers);
    }

    if (!name || !email || !message || !interest) {
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

    try {
      await deliverEmail(context.env, payload);
    } catch (err) {
      console.error("email_delivery_failed", err && err.code, err && err.message);
      return json(
        { ok: false, error: "email_failed", contactEmail: CONTACT_EMAIL },
        502,
        headers
      );
    }

    context.waitUntil(notifyWebhook(context.env, payload));
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

export async function onRequestHead() {
  return new Response(null, { status: 204, headers: { "Cache-Control": "no-store", Allow: "POST, OPTIONS" } });
}

export default {
  async fetch(request, env, ctx) {
    const context = { request, env, waitUntil: ctx.waitUntil.bind(ctx) };
    if (request.method === "OPTIONS") return onRequestOptions(context);
    if (request.method === "HEAD") return onRequestHead();
    if (request.method === "POST") return onRequestPost(context);
    return onRequestGet();
  },
};
