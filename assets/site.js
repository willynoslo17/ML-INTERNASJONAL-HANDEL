(function () {
  const CONTACT_EMAIL = "willynoslo17@gmail.com";
  const COOKIE_KEY = "ml-cookie-consent";

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function initCookieBanner() {
    const banner = qs("#cookie-banner");
    if (!banner) return;
    if (localStorage.getItem(COOKIE_KEY)) return;
    banner.classList.add("show");

    const accept = qs("[data-cookie-accept]", banner);
    const necessary = qs("[data-cookie-necessary]", banner);
    function save(value) {
      localStorage.setItem(COOKIE_KEY, value);
      banner.classList.remove("show");
    }
    if (accept) accept.addEventListener("click", function () { save("all"); });
    if (necessary) necessary.addEventListener("click", function () { save("necessary"); });
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
      const lang = document.documentElement.lang || "no";
      const t = messages[lang] || messages.no;

      if (status) {
        status.className = "form-status";
        status.textContent = t.sending;
      }
      if (submitBtn) submitBtn.disabled = true;

      const data = {
        name: form.name.value.trim(),
        email: form.email.value.trim(),
        company: form.company ? form.company.value.trim() : "",
        interest: form.interest ? form.interest.value.trim() : "",
        message: form.message.value.trim(),
        website: form.website ? form.website.value.trim() : "",
        lang: lang,
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
          form.reset();
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

  document.addEventListener("DOMContentLoaded", function () {
    initCookieBanner();
    initContactForm();
  });
})();
