// Enlaces de pago (Stripe Payment Links o Checkout). VACÍOS = aún no hay cobro online.
// Cuando José cree los enlaces en Stripe (ver docs/PRICING.md en ML-TRADE-APPS), pegar aquí la URL de cada plan.
window.ML_CHECKOUT_LINKS = {
  tollvik_monthly: '',
  tollvik_yearly: '',
  kildevik_monthly: '',
  kildevik_yearly: '',
  kursvik_monthly: '',
  kursvik_yearly: '',
};
document.addEventListener('click', function (e) {
  var b = e.target.closest('[data-plan]');
  if (!b) return;
  e.preventDefault();
  var url = (window.ML_CHECKOUT_LINKS || {})[b.getAttribute('data-plan')];
  if (url) { window.location.href = url; return; }
  var n = document.getElementById('notice-' + b.getAttribute('data-plan'));
  if (n) n.style.display = 'block';
});
