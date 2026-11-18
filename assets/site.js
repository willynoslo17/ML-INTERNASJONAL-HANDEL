(function () {
  document.documentElement.classList.add("js");
  const CONTACT_EMAIL = "info@mlinternasjonal.no";
  // Permanent: never add tel: or phone numbers on this site.
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
      text: "Vi bruker nødvendige tekniske informasjonskapsler og lagrer opprinnelsen til besøket ditt (kilde og inngangsside) i nettleseren bare for å vite hvor henvendelsene fra skjemaet kommer fra.",
      accept: "Godta",
      reject: "Avvis",
      policy: "Informasjonskapselpolicy",
      policyHref: "/cookies/",
    },
    en: {
      text: "We use necessary technical cookies and store the origin of your visit (source and entry page) in the browser only to know where form contacts come from.",
      accept: "Accept",
      reject: "Reject",
      policy: "Cookie Policy",
      policyHref: "/en/cookies/",
    },
    es: {
      text: "Usamos cookies técnicas necesarias y guardamos en el navegador el origen de tu visita (fuente y página de entrada) solo para saber de dónde llegan los contactos del formulario.",
      accept: "Aceptar",
      reject: "Rechazar",
      policy: "Política de cookies",
      policyHref: "/es/cookies/",
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
      "<p>" + copy.text + "</p>" +
      '<div class="cookie-actions">' +
      '<button class="btn solid" type="button" data-cookie-accept>' + copy.accept + "</button>" +
      '<button class="btn" type="button" data-cookie-reject>' + copy.reject + "</button>" +
      '<a class="btn" href="' + copy.policyHref + '">' + copy.policy + "</a>" +
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
        ok: "Takk for meldingen. Vi tar kontakt snart.",
        err: "Meldingen kunne ikke sendes. Prøv igjen eller skriv til oss på info@mlinternasjonal.no.",
      },
      en: {
        sending: "Sending…",
        ok: "Thank you for your message. We will get back to you soon.",
        err: "The message could not be sent. Please try again or write to us at info@mlinternasjonal.no.",
      },
      es: {
        sending: "Enviando…",
        ok: "Gracias por tu mensaje. Te contactaremos pronto.",
        err: "No se pudo enviar el mensaje. Inténtalo de nuevo o escríbenos a info@mlinternasjonal.no.",
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
          if (status) {
            status.className = "form-status err";
            status.innerHTML = t.err.replace(
              /info@mlinternasjonal\.no/g,
              '<a href="mailto:info@mlinternasjonal.no">info@mlinternasjonal.no</a>'
            );
          }
        }
      } catch (err) {
        if (status) {
          status.className = "form-status err";
          status.innerHTML = t.err.replace(
            /info@mlinternasjonal\.no/g,
            '<a href="mailto:info@mlinternasjonal.no">info@mlinternasjonal.no</a>'
          );
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
  });
})();
