(() => {
  'use strict';
  const slides = [...document.querySelectorAll('.slide-shell')];
  const dots = [...document.querySelectorAll('.slide-dot')];
  const counter = document.querySelector('[data-counter]');
  const label = document.querySelector('[data-current-title]');
  const prev = document.querySelector('[data-prev]');
  const next = document.querySelector('[data-next]');
  const overviewButton = document.querySelector('[data-overview]');
  const fullscreenButton = document.querySelector('[data-fullscreen]');
  const help = document.querySelector('dialog');
  let current = 0;
  const updateScales = () => slides.forEach(shell => {
    if (shell.clientWidth) shell.style.setProperty('--slide-scale', shell.clientWidth / 1280);
  });
  new ResizeObserver(updateScales).observe(document.querySelector('.stage'));
  function show(index, writeHash = true) {
    current = Math.max(0, Math.min(slides.length - 1, index));
    slides.forEach((shell, i) => {
      shell.classList.toggle('is-active', i === current);
      const hidden = !document.body.classList.contains('is-overview') && i !== current;
      shell.setAttribute('aria-hidden', String(hidden));
      shell.inert = hidden;
      dots[i].setAttribute('aria-current', String(i === current));
    });
    counter.textContent = `${String(current + 1).padStart(2, '0')} / ${String(slides.length).padStart(2, '0')}`;
    label.textContent = slides[current].dataset.title;
    prev.disabled = current === 0;
    next.disabled = current === slides.length - 1;
    if (writeHash) history.replaceState(null, '', `#slide-${current + 1}`);
    requestAnimationFrame(updateScales);
  }
  function overview(force) {
    const active = force ?? !document.body.classList.contains('is-overview');
    document.body.classList.toggle('is-overview', active);
    overviewButton.setAttribute('aria-pressed', String(active));
    show(current, false);
    requestAnimationFrame(updateScales);
    if (!active) window.scrollTo({top:0});
  }
  async function fullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      fullscreenButton.setAttribute('title','Tela cheia indisponível neste visualizador. Abra o HTML no navegador.');
      document.querySelector('[data-announcement]').textContent='Tela cheia indisponível neste visualizador. Abra o HTML no navegador.';
    }
  }
  prev.addEventListener('click', () => show(current - 1));
  next.addEventListener('click', () => show(current + 1));
  dots.forEach((dot, i) => dot.addEventListener('click', () => {overview(false); show(i);}));
  slides.forEach((shell, i) => shell.addEventListener('click', () => {
    if(document.body.classList.contains('is-overview')) {overview(false); show(i);}
  }));
  overviewButton.addEventListener('click', () => overview());
  fullscreenButton.addEventListener('click', fullscreen);
  document.querySelector('[data-print]').addEventListener('click', () => window.print());
  document.querySelector('[data-help]').addEventListener('click', () => help.showModal());
  document.querySelector('[data-close-help]').addEventListener('click', () => help.close());
  document.addEventListener('fullscreenchange', () => {
    fullscreenButton.setAttribute('aria-pressed', String(Boolean(document.fullscreenElement)));
    requestAnimationFrame(updateScales);
  });
  window.addEventListener('keydown', event => {
    if (help.open || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName) || event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key === ' ' && event.target.closest('button,a')) return;
    if (['ArrowRight','ArrowDown','PageDown',' '].includes(event.key)) {event.preventDefault(); show(current + 1);}
    else if (['ArrowLeft','ArrowUp','PageUp'].includes(event.key)) {event.preventDefault(); show(current - 1);}
    else if (event.key === 'Home') {event.preventDefault(); show(0);}
    else if (event.key === 'End') {event.preventDefault(); show(slides.length - 1);}
    else if (event.key.toLowerCase() === 'g') overview();
    else if (event.key.toLowerCase() === 'f') fullscreen();
    else if (event.key === '?') help.showModal();
    else if (event.key === 'Escape') overview(false);
  });
  function readHash() {
    const match = location.hash.match(/^#slide-(\d+)$/);
    show(match ? Number(match[1]) - 1 : 0, false);
  }
  window.addEventListener('hashchange', readHash);
  window.addEventListener('beforeprint', () => slides.forEach(shell => {shell.inert = false; shell.setAttribute('aria-hidden','false');}));
  window.addEventListener('afterprint', () => show(current, false));
  readHash();
  document.fonts.ready.then(updateScales);
})();
