/**
 * Single source of contact/social config for mlinternasjonal.no
 * Public contact policy (AGENTS.md): WhatsApp + email only — no tel: / phone display.
 * Numbers below document the correct line (+47 922 11 752). Do not use any other phone line.
 */
window.SITE_CONFIG = {
  legalName: "MARTINEZ LOZANO INTERNASJONAL HANDEL (ENK)",
  brandName: "ML Internasjonal Handel",
  orgNr: "935 407 095 MVA",
  orgNrDigits: "935407095",
  siteUrl: "https://mlinternasjonal.no",
  email: "willynoslo17@gmail.com",
  address: {
    streetAddress: "Norbygata 19",
    postalCode: "0187",
    addressLocality: "Oslo",
    addressCountry: "NO",
  },
  whatsapp: {
    e164: "+4792211752",
    display: "+47 922 11 752",
    url: "https://wa.me/4792211752",
  },
  /**
   * Call / SMS line (same number as WhatsApp). Documented only —
   * do not render tel: links or visible phone numbers on this site.
   */
  phone: {
    e164: "+4792211752",
    display: "+47 922 11 752",
    tel: "tel:+4792211752",
    renderOnSite: false,
  },
  /**
   * Social URLs. Entries with url null / [CONFIRMAR] must not be rendered.
   */
  socials: [
    {
      id: "instagram",
      label: "Instagram",
      url: "https://www.instagram.com/willmart24",
    },
    {
      id: "youtube",
      label: "YouTube",
      url: null, // [CONFIRMAR URL]
    },
  ],
  responsiblePerson: {
    label: "Willy Martinez",
    url: "https://willymartinez.no",
  },
};
