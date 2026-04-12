(function () {
    'use strict';

    const SUPPORTS_IO = 'IntersectionObserver' in window;


    function initScrollReveal() {
        const selector = '[data-sa],[data-aos],.reveal,.reveal-fade,.reveal-zoom';
        const els = document.querySelectorAll(selector);

        if (!SUPPORTS_IO) {
            els.forEach(el => revealEl(el, 0));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const delay = parseInt(
                        el.dataset.saDelay || el.dataset.aosDelay || el.dataset.delay || '0',
                        10
                    );
                    setTimeout(() => revealEl(el, delay), 0);
                    observer.unobserve(el);
                }
            });
        }, {
            threshold: 0,
            rootMargin: '0px 0px -40px 0px'
        });

        els.forEach(el => {

            const rect = el.getBoundingClientRect();
            if (rect.top < window.innerHeight && rect.bottom > 0) {
                const delay = parseInt(
                    el.dataset.saDelay || el.dataset.aosDelay || el.dataset.delay || '0',
                    10
                );
                setTimeout(() => revealEl(el, 0), delay);
            } else {
                observer.observe(el);
            }
        });
    }

    function revealEl(el, _delay) {
        el.classList.add('sa-done', 'active', 'aos-animate');
    }


    function initStagger() {
        const containers = document.querySelectorAll('.sa-stagger');
        if (!containers.length) return;

        if (!SUPPORTS_IO) {
            containers.forEach(revealStagger);
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    revealStagger(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0,
            rootMargin: '0px 0px -40px 0px'
        });

        containers.forEach(container => {
            const rect = container.getBoundingClientRect();
            if (rect.top < window.innerHeight && rect.bottom > 0) {
                revealStagger(container);
            } else {
                observer.observe(container);
            }
        });
    }

    function revealStagger(container) {
        const children = Array.from(container.children);
        const baseDelay = parseInt(container.getAttribute('data-stagger-delay') || '80', 10);

        children.forEach((child, i) => {
            setTimeout(() => {
                child.classList.add('sa-done');
            }, i * baseDelay);
        });
    }


    function initCounters() {
        if (!SUPPORTS_IO) return;
        const els = document.querySelectorAll('[data-count]');
        if (!els.length) return;

        const obs = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        els.forEach(el => obs.observe(el));
    }

    function animateCounter(el) {
        const target = parseFloat(el.dataset.count);
        const suffix = el.dataset.suffix || '';
        const isFloat = (target % 1 !== 0);
        const duration = 1500;
        const start = performance.now();

        function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            const ease = 1 - Math.pow(1 - progress, 5);
            const val = target * ease;
            el.textContent = (isFloat ? val.toFixed(1) : Math.floor(val).toLocaleString('uk-UA')) + suffix;
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }


    function initScrollProgress() {
        const bar = document.getElementById('scroll-progress-bar');
        if (!bar) return;
        window.addEventListener('scroll', () => {
            const h = document.documentElement;
            const pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
            bar.style.width = Math.min(pct, 100) + '%';
        }, { passive: true });
    }


    function initAlertDismiss() {
        document.querySelectorAll('.alert').forEach(alert => {
            setTimeout(() => {
                alert.style.transition = 'opacity 0.6s ease, transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(30px)';
                setTimeout(() => alert.remove(), 600);
            }, 6000);
        });
    }


    function boot() {
        initScrollReveal();
        initStagger();
        initCounters();
        initScrollProgress();
        initAlertDismiss();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

})();
