(function () {
  document.documentElement.classList.add("js");
  const CONTACT_EMAIL = "info@mlinternasjonal.no";
  // Permanent: WhatsApp only — never add tel: or phone numbers on this site.
  const WHATSAPP_BASE = "https://wa.me/4792211752";
  const WHATSAPP_TEXT = {
    es: "Hola ML Internasjonal Handel",
    no: "Hei ML Internasjonal Handel",
    en: "Hello ML Internasjonal Handel",
  };
  const COOKIE_KEY = "ml-cookie-consent";

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  const PIXEL_ID = "1425772629175058";
  function loadPixel() {
    if (window.fbq) return;
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    window.fbq('init', PIXEL_ID);
    window.fbq('track', 'PageView');
  }

  function pageLang() {
    const lang = (document.documentElement.lang || "").slice(0, 2);
    if (lang === "es" || lang === "en" || lang === "no") return lang;
    const path = location.pathname || "";
    if (path.indexOf("/es/") === 0) return "es";
    if (path.indexOf("/en/") === 0) return "en";
    return "no";
  }

  const COOKIE_COPY = {
    no: {
      html: "Vi bruker nødvendige informasjonskapsler for at nettstedet skal fungere. Hvis du godtar, bruker vi også Meta-pikselen (Facebook) for å måle besøk. Du kan godta eller avvise valgfrie informasjonskapsler. Les mer i <a href=\"/cookies/\">cookie-erklæringen</a> og i <a href=\"/personvern/\">personvernerklæringen</a>.",
      accept: "Godta",
      reject: "Avvis",
    },
    en: {
      html: "We use necessary cookies for the site to work. If you accept, we also use the Meta (Facebook) Pixel to measure visits. You can accept or reject optional cookies. Read more in our <a href=\"/en/cookies/\">cookie policy</a> and <a href=\"/en/privacy/\">privacy policy</a>.",
      accept: "Accept",
      reject: "Reject",
    },
    es: {
      html: "Usamos cookies necesarias para que el sitio funcione. Si aceptas, también usamos el píxel de Meta (Facebook) para medir las visitas. Puedes aceptar o rechazar las cookies opcionales. Más información en la <a href=\"/es/cookies/\">política de cookies</a> y en la <a href=\"/es/privacidad/\">política de privacidad</a>.",
      accept: "Aceptar",
      reject: "Rechazar",
    },
  };

  function ensureCookieBanner() {
    let banner = qs("#cookie-banner");
    if (banner) return banner;
    const copy = COOKIE_COPY[pageLang()] || COOKIE_COPY.no;
    banner = document.createElement("div");
    banner.id = "cookie-banner";
    banner.className = "cookie-banner";
    banner.setAttribute("role", "dialog");
    banner.setAttribute("aria-live", "polite");
    banner.setAttribute("aria-label", "Cookies");
    banner.innerHTML =
      "<p>" + copy.html + "</p>" +
      '<div class="cookie-actions">' +
      '<button class="btn solid" type="button" data-cookie-accept>' + copy.accept + "</button>" +
      '<button class="btn" type="button" data-cookie-reject>' + copy.reject + "</button>" +
      "</div>";
    document.body.appendChild(banner);
    return banner;
  }

  function initCookieBanner() {
    if (localStorage.getItem(COOKIE_KEY) === "all") loadPixel();
    const banner = ensureCookieBanner();
    const reset = document.querySelector("[data-cookie-reset]");
    if (reset) {
      reset.addEventListener("click", function () {
        localStorage.removeItem(COOKIE_KEY);
        location.reload();
      });
    }
    if (localStorage.getItem(COOKIE_KEY)) return;
    banner.classList.add("show");

    function save(value) {
      localStorage.setItem(COOKIE_KEY, value);
      banner.classList.remove("show");
    }
    const accept = qs("[data-cookie-accept]", banner);
    const reject = qs("[data-cookie-reject]", banner) || qs("[data-cookie-necessary]", banner);
    if (accept) accept.addEventListener("click", function () { save("all"); loadPixel(); });
    if (reject) reject.addEventListener("click", function () { save("necessary"); });
  }

  function initContactForm() {
    const form = qs("#contact-form");
    if (!form) return;
    const status = qs("#form-status");
    const submitBtn = qs("[type=submit]", form);

    const messages = {
      no: {
        sending: "Sender…",
        ok: "Takk. Meldingen er sendt.",
        err: "Kunne ikke sende. Skriv til ",
      },
      en: {
        sending: "Sending…",
        ok: "Thank you. Your message has been sent.",
        err: "Could not send. Please email ",
      },
      es: {
        sending: "Enviando…",
        ok: "Gracias. Tu mensaje ha sido enviado.",
        err: "No se pudo enviar. Escribe a ",
      },
    };

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const lang = document.documentElement.lang || "no";
      const t = messages[lang] || messages.no;

      if (status) {
        status.className = "form-status";
        status.textContent = t.sending;
      }
      if (submitBtn) submitBtn.disabled = true;

      fillLeadFields(form);
      const data = {
        sector: form.sector ? form.sector.value.trim() : "",
        service: form.service ? form.service.value.trim() : "",
        name: form.name.value.trim(),
        company: form.company ? form.company.value.trim() : "",
        country: form.country ? form.country.value.trim() : "",
        email: form.email.value.trim(),
        consulta: (form.consulta || form.message).value.trim(),
        website: form.website ? form.website.value.trim() : "",
        lang: lang,
        utm_source: form.utm_source ? form.utm_source.value.trim() : "",
        utm_medium: form.utm_medium ? form.utm_medium.value.trim() : "",
        utm_campaign: form.utm_campaign ? form.utm_campaign.value.trim() : "",
        referrer: form.referrer ? form.referrer.value.trim() : "",
        landing_page: form.landing_page ? form.landing_page.value.trim() : "",
        submit_page: form.submit_page ? form.submit_page.value.trim() : "",
        first_visit: form.first_visit ? form.first_visit.value.trim() : "",
      };

      try {
        const res = await fetch("/api/lead", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        const json = await res.json().catch(function () { return { ok: false }; });
        if (res.ok && json.ok) {
          if (status) {
            status.className = "form-status ok";
            status.textContent = t.ok;
          }
          if (window.fbq) window.fbq("track", "Lead");
          form.reset();
          fillLeadFields(form);
        } else {
          const email = json.contactEmail || CONTACT_EMAIL;
          if (status) {
            status.className = "form-status err";
            status.innerHTML = t.err + '<a href="mailto:' + email + '">' + email + "</a>";
          }
        }
      } catch (err) {
        if (status) {
          status.className = "form-status err";
          status.innerHTML = t.err + '<a href="mailto:' + CONTACT_EMAIL + '">' + CONTACT_EMAIL + "</a>";
        }
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  function initHeader() {
    const header = qs(".site-header");
    if (!header) return;
    const toggle = qs(".nav-toggle", header);
    const nav = qs("#site-nav", header);

    const solidHeader = !document.querySelector(".hero");
    function onScroll() {
      header.classList.toggle("is-stuck", solidHeader || window.scrollY > 8);
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    function closeNav() {
      header.classList.remove("is-open");
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    }
    function openNav() {
      header.classList.add("is-open");
      if (toggle) toggle.setAttribute("aria-expanded", "true");
    }

    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        if (header.classList.contains("is-open")) closeNav();
        else openNav();
      });
      nav.addEventListener("click", function (e) {
        if (e.target.closest("a")) closeNav();
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeNav();
      });
      window.addEventListener("resize", function () {
        if (window.innerWidth > 899) closeNav();
      });
    }
  }

  function initReveal() {
    const nodes = document.querySelectorAll("[data-reveal]");
    if (!nodes.length) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      nodes.forEach(function (node) { node.classList.add("is-in"); });
      return;
    }
    if (!("IntersectionObserver" in window)) {
      nodes.forEach(function (node) { node.classList.add("is-in"); });
      return;
    }
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      });
    }, { threshold: 0.16, rootMargin: "0px 0px -8% 0px" });
    nodes.forEach(function (node) { io.observe(node); });
    setTimeout(function () {
      nodes.forEach(function (node) { node.classList.add("is-in"); });
    }, 700);
  }

  function whatsappUrl() {
    const lang = (document.documentElement.lang || "no").slice(0, 2);
    const text = WHATSAPP_TEXT[lang] || WHATSAPP_TEXT.es;
    return WHATSAPP_BASE + "?text=" + encodeURIComponent(text);
  }

  function initWhatsAppLinks() {
    const href = whatsappUrl();
    document.querySelectorAll('a[href^="https://wa.me/4792211752"]').forEach(function (link) {
      if (link.href.indexOf("text=") === -1) link.href = href;
    });
    document.querySelectorAll(".wa-float").forEach(function (el) { el.remove(); });
  }


  var LEAD_TOUCH_KEY = "ml-lead-first-touch";

  function leadParam(params, name) {
    var value = params.get(name);
    return value ? String(value).slice(0, 200) : "";
  }

  function currentPageUrl() {
    return window.location.origin + window.location.pathname + window.location.search + window.location.hash;
  }

  function captureFirstTouch() {
    try {
      var stored = window.localStorage.getItem(LEAD_TOUCH_KEY);
      if (stored) return JSON.parse(stored);
    } catch (err) {}
    var params = new URLSearchParams(window.location.search);
    var touch = {
      utm_source: leadParam(params, "utm_source"),
      utm_medium: leadParam(params, "utm_medium"),
      utm_campaign: leadParam(params, "utm_campaign"),
      referrer: document.referrer ? String(document.referrer).slice(0, 500) : "",
      landing_page: currentPageUrl().slice(0, 500),
      first_visit: new Date().toISOString()
    };
    try {
      window.localStorage.setItem(LEAD_TOUCH_KEY, JSON.stringify(touch));
    } catch (err) {}
    return touch;
  }

  function fillLeadFields(form) {
    var touch = captureFirstTouch() || {};
    var map = {
      utm_source: touch.utm_source || "",
      utm_medium: touch.utm_medium || "",
      utm_campaign: touch.utm_campaign || "",
      referrer: touch.referrer || "",
      landing_page: touch.landing_page || "",
      first_visit: touch.first_visit || "",
      submit_page: currentPageUrl().slice(0, 500)
    };
    Object.keys(map).forEach(function (name) {
      var input = form.querySelector('[name="' + name + '"]');
      if (input) input.value = map[name];
    });
  }

  function initLeadTracking() {
    captureFirstTouch();
    document.querySelectorAll("#contact-form, form[data-contact-form]").forEach(function (form) {
      fillLeadFields(form);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initHeader();
    initReveal();
    initCookieBanner();
    initLeadTracking();
    initContactForm();
    initWhatsAppLinks();
  });
})();
