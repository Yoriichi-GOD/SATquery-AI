/* Shared fixed-header measurements and pointer-only navigation feedback. No analytical state. */
(() => {
  'use strict';
  const header = document.querySelector('body > header');
  if (!header) return;
  const root = document.documentElement;
  const footer = document.querySelector('body > footer');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let animation = null, revision = 0;
  const cancel = () => {revision++; if (animation) animation.cancel(); animation = null;};
  const measure = () => {
    const height = Math.ceil(header.getBoundingClientRect().height);
    if (height > 0 && root.style.getPropertyValue('--sq-header-h') !== height + 'px') {
      root.style.setProperty('--sq-header-h', height + 'px');
    }
    const footerHeight = footer ? Math.max(0, Math.ceil(footer.getBoundingClientRect().height)) : 0;
    if (root.style.getPropertyValue('--sq-scroll-footer-h') !== footerHeight + 'px') {
      root.style.setProperty('--sq-scroll-footer-h', footerHeight + 'px');
    }
  };
  if (typeof ResizeObserver !== 'undefined') {
    const observer = new ResizeObserver(measure);
    observer.observe(header); if (footer) observer.observe(footer);
  }
  window.addEventListener('resize', measure, {passive:true});
  document.fonts?.ready.then(measure);
  measure();
  document.addEventListener('pointerdown', () => {root.dataset.sqInput = 'pointer';}, true);
  document.addEventListener('keydown', () => {root.dataset.sqInput = 'keyboard'; cancel();}, true);
  reduced.addEventListener?.('change', cancel);
  header.addEventListener('click', event => {
    // Keyboard and scripted clicks have detail=0; repeated navigation must never delay them.
    if (!event.detail || reduced.matches || !event.target.closest('nav button')) return;
    cancel();
    const ticket = revision;
    requestAnimationFrame(() => {
      if (ticket !== revision || reduced.matches) return;
      const section = [...document.querySelectorAll('main > section')].find(node => !node.hidden);
      if (!section || typeof section.animate !== 'function') return;
      animation = section.animate([{opacity:.86,transform:'translateY(4px)'},{opacity:1,transform:'none'}],
        {duration:180,easing:'cubic-bezier(0.16, 1, 0.3, 1)'});
    });
  });
})();
