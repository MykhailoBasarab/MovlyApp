
document.addEventListener('DOMContentLoaded', function () {

    const saEls = document.querySelectorAll('[data-sa]');
    if (saEls.length && 'IntersectionObserver' in window) {
        const saObs = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('sa-done');
                    
                    if (entry.target.classList.contains('sa-grid-stagger')) {
                        const children = entry.target.children;
                        Array.from(children).forEach((child, i) => {
                            setTimeout(() => {
                                child.style.opacity = '1';
                                child.style.transform = 'none';
                                child.style.filter = 'none';
                            }, i * 150);
                        });
                    }
                    saObs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
        
        saEls.forEach(el => saObs.observe(el));
    }

    function animateCounter(el) {
        const target = parseFloat(el.dataset.count);
        const suffix = el.dataset.suffix || '';
        const isFloat = (target % 1 !== 0);
        const start = performance.now();
        const duration = 1800;

        function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            const ease = 1 - Math.pow(1 - progress, 4);                                                                                                                                                     
            const currentVal = target * ease;
            
            el.textContent = (isFloat ? currentVal.toFixed(1) : Math.floor(currentVal).toLocaleString('uk-UA')) + suffix;
            
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    const cntEls = document.querySelectorAll('[data-count]');
    if (cntEls.length && 'IntersectionObserver' in window) {
        const cntObs = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    cntObs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.6 });
        cntEls.forEach(el => cntObs.observe(el));
    }

    // 3. Scroll Progress Bar
    const progressBar = document.getElementById('scroll-progress-bar');
    if (progressBar) {
        window.addEventListener('scroll', () => {
            const h = document.documentElement;
            const b = document.body;
            const st = 'scrollTop';
            const sh = 'scrollHeight';
            const pct = (h[st] || b[st]) / ((h[sh] || b[sh]) - h.clientHeight) * 100;
            progressBar.style.width = Math.min(pct, 100) + '%';
        }, { passive: true });
    }
});
