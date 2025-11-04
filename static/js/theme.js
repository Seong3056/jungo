(function () {
  const root = document.documentElement,
    KEY = 'theme-pref',
    media = window.matchMedia('(prefers-color-scheme: dark)');

  function apply(t) {
    root.setAttribute('data-theme', t === 'system' ? (media.matches ? 'dark' : 'light') : t);
  }

  function setActive(t) {
    document.querySelectorAll('[data-theme-set]').forEach(b => b.classList.toggle('btn--active', b.dataset.themeSet === t));
  }

  function load() {
    const s = localStorage.getItem(KEY) || 'system';
    apply(s);
    setActive(s);
  }

  function save(t) {
    localStorage.setItem(KEY, t);
    apply(t);
    setActive(t);
  }
  media.addEventListener('change', () => {
    const s = localStorage.getItem(KEY) || 'system';
    if (s === 'system') apply('system');
  });
  window.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-theme-set]').forEach(btn => btn.addEventListener('click', () => save(btn.dataset.themeSet)));
    load();
  });
  const mobileToggle = document.getElementById("mobile-theme-toggle");
  if (mobileToggle) {
    mobileToggle.addEventListener("click", () => {
      console.log('click');

      const current = localStorage.getItem(KEY) || 'system';
      const next = current === 'dark' ? 'light' : 'dark';
      save(next);
    });
  }
})();