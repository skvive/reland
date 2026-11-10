'use strict';
/* RE:LAND Kang Class: screenshot layout interactions, preserving blog.js/60 lessons/30 Q&A. */
(() => {
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];
  const lectures = Array.isArray(window.KANG_DATA?.lectures) ? window.KANG_DATA.lectures : [];
  const catalog = $('#allLessons');
  const sources = $('#sources');
  const search = $('#search');

  function openCatalog(query = '') {
    if (!catalog || !search) return;
    catalog.hidden = false;
    if (query) {
      const all = $$('#tags .tag').find(b => b.textContent.trim() === '전체');
      if (all) all.click();
      search.value = query;
      search.dispatchEvent(new Event('input', { bubbles: true }));
    }
    catalog.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    if (query) search.focus({ preventScroll: true });
  }

  $$('[data-open-catalog]').forEach(btn => btn.addEventListener('click', () => openCatalog()));
  $$('[data-open-sources]').forEach(btn => btn.addEventListener('click', () => {
    if (!sources) return;
    sources.hidden = false;
    sources.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }));

  const topForm = $('#globalSearchForm');
  if (topForm) topForm.addEventListener('submit', event => {
    event.preventDefault();
    const q = ($('#globalSearch')?.value || '').trim();
    openCatalog(q);
  });

  function openLecture(id) {
    const lecture = lectures.find(x => x.id === id);
    if (!lecture || !search) return;
    const all = $$('#tags .tag').find(b => b.textContent.trim() === '전체');
    if (all) all.click();
    search.value = lecture.title;
    search.dispatchEvent(new Event('input', { bubbles: true }));
    const target = $$('#lessonGrid [data-lesson]').find(btn => Number(btn.dataset.lesson) === id);
    if (target) {
      target.click();
    } else {
      openCatalog(lecture.title);
    }
  }
  $$('[data-preview-lesson]').forEach(btn => btn.addEventListener('click', () => {
    openLecture(Number(btn.dataset.previewLesson));
  }));
  const row = $('#featureCards');
  function scrollCourses(direction) {
    if (!row) return;
    const firstCard = row.querySelector('.feature-card');
    const distance = firstCard ? firstCard.getBoundingClientRect().width + 9 : 270;
    row.scrollBy({ left: direction * distance, behavior: 'smooth' });
  }
  $('#featurePrev')?.addEventListener('click', () => scrollCourses(-1));
  $('#featureNext')?.addEventListener('click', () => scrollCourses(1));

  const faq = $('#questions');
  const faqExpand = $('#faqExpand');
  if (faq && faqExpand) {
    faqExpand.setAttribute('aria-expanded', 'false');
    faqExpand.addEventListener('click', () => {
      const expanded = faq.classList.toggle('faq-expanded');
      faqExpand.setAttribute('aria-expanded', String(expanded));
      faqExpand.textContent = expanded ? '접기 ↑' : '전체 보기 →';
    });
  }
  $('#menuBtn')?.addEventListener('click', () => {
    const isOpen = $('.head-row nav')?.classList.contains('open');
    $('#menuBtn').setAttribute('aria-expanded', String(!!isOpen));
  });
  // Maintain utility panels when a URL is copied with a deep-link fragment.
  if (location.hash === '#allLessons') catalog && (catalog.hidden = false);
  if (location.hash === '#sources') sources && (sources.hidden = false);
})();