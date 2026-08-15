// ===========================================================
// WIRELINE — Dark mode toggle (UI layer only)
// This file only switches the visual theme and remembers the
// choice locally. It has no involvement in the TCP/socket logic
// that the networking teammate will wire up separately.
// ===========================================================

(function () {
  const root = document.documentElement;
  const STORAGE_KEY = 'wireline-theme';

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    document.querySelectorAll('.theme-toggle').forEach((btn) => {
      btn.setAttribute('aria-checked', theme === 'dark');
    });
  }

  function currentTheme() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  // Load saved preference (falls back to system preference once)
  const saved = localStorage.getItem(STORAGE_KEY);
  const preferred = saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  applyTheme(preferred);

  // Enable transitions only after the initial theme is set,
  // so the first paint doesn't animate.
  requestAnimationFrame(() => root.classList.add('theme-ready'));

  document.addEventListener('click', (e) => {
    const toggle = e.target.closest('.theme-toggle');
    if (!toggle) return;
    const next = currentTheme() === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem(STORAGE_KEY, next);
  });
})();
