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


function clip(value, max) {
  return String(value || "").replace(/[\r\n]+/g, " ").trim().slice(0, max);
}

function formatLima(iso) {
  const date = iso ? new Date(iso) : new Date();
  if (Number.isNaN(date.getTime())) return String(iso || "—");
  try {
    return (
      new Intl.DateTimeFormat("es-PE", {
        timeZone: "America/Lima",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      }).format(date) + " (America/Lima)"
    );
  } catch (err) {
    return date.toISOString();
  }
}

function deviceFromUa(ua) {
  const s = String(ua || "").toLowerCase();
  if (!s) return "—";
  if (/ipad|tablet|playbook|silk/.test(s)) return "Tablet";
  if (/mobi|iphone|android.*mobile|windows phone|opera mini/.test(s)) return "Móvil";
  return "Escritorio";
}

function deriveOrigen(payload) {
  const hay = [
    payload.utm_source,
    payload.utm_medium,
    payload.utm_campaign,
    payload.referrer,
    payload.landing_page,
  ]
    .join(" ")
    .toLowerCase();
  if (/(instagram|\big\b|ig\.me)/.test(hay)) return "Instagram";
  if (/(facebook|fb\.com|fbclid|\bfb\b)/.test(hay)) return "Facebook";
  if (/(linkedin|lnkd\.in)/.test(hay)) return "LinkedIn";
  if (/(whatsapp|wa\.me|\bwa\b)/.test(hay)) return "WhatsApp";
  if (/(google|gclid|googleapis)/.test(hay)) return "Google";
  if (!String(payload.utm_source || "").trim() && !String(payload.referrer || "").trim()) {
    return "Directo";
  }
  return "Otro";
}

function attributionFrom(request, body) {
  const cf = request.cf || {};
  const ua = request.headers.get("User-Agent") || "";
  const submittedAt = new Date().toISOString();
  return {
    utm_source: clip(body.utm_source, 200),
    utm_medium: clip(body.utm_medium, 200),
    utm_campaign: clip(body.utm_campaign, 200),
    referrer: clip(body.referrer, 500),
    landing_page: clip(body.landing_page, 500),
    submit_page: clip(body.submit_page, 500),
    first_visit: clip(body.first_visit, 80),
    cf_country: clip(cf.country, 80),
    cf_city: clip(cf.city, 120),
    user_agent: clip(ua, 400),
    device: deviceFromUa(ua),
    submittedAt,
    origen: "",
  };
}

function letter(payload) {
  const origen = deriveOrigen(payload);
  return [
    "Sector: " + payload.sector,
    "Servicio: " + payload.service,
    "Nombre: " + payload.name,
    "Empresa: " + (payload.company || "—"),
    "País: " + (payload.country || "—"),
    "Correo: " + payload.email,
    "",
    "Consulta:",
    payload.consulta,
    "",
    "======= Origen del contacto =======",
    "Origen: " + origen,
    "UTM source: " + (payload.utm_source || "—"),
    "UTM medium: " + (payload.utm_medium || "—"),
    "UTM campaign: " + (payload.utm_campaign || "—"),
    "Referrer: " + (payload.referrer || "—"),
    "Página de aterrizaje: " + (payload.landing_page || "—"),
    "Página de envío: " + (payload.submit_page || "—"),
    "Primera visita: " + (payload.first_visit ? formatLima(payload.first_visit) : "—"),
    "País (Cloudflare): " + (payload.cf_country || "—"),
    "Ciudad (Cloudflare): " + (payload.cf_city || "—"),
    "Dispositivo: " + (payload.device || "—"),
    "User-Agent: " + (payload.user_agent || "—"),
    "Hora de envío: " + formatLima(payload.submittedAt),
  ].join("\n");
}

async function deliverEmail(env, payload) {
  if (!env.EMAIL || typeof env.EMAIL.send !== "function") {
    throw new Error("email_binding_missing");
  }
  const to = env.CONTACT_INBOX || CONTACT_EMAIL;
  const subject = "Consulta mlinternasjonal.no (" + oneLine(payload.sector) + ") — " + oneLine(payload.name);
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
    const sector = String(body.sector || "").trim();
    const service = String(body.service || "").trim();
    const name = String(body.name || "").trim();
    const company = String(body.company || "").trim();
    const country = String(body.country || body.pais || "").trim();
    const email = String(body.email || "").trim();
    const consulta = String(body.consulta || body.message || "").trim();
    const lang = String(body.lang || "no").trim();
    const website = String(body.website || "").trim(); // honeypot

    if (website) {
      return json({ ok: true }, 200, headers);
    }

    if (!sector || !service || !name || !email || !consulta) {
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
      sector,
      service,
      name,
      company,
      country,
      email,
      consulta,
      lang,
      ...attributionFrom(context.request, body),
    };
    payload.origen = deriveOrigen(payload);

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
