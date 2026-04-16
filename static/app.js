/* ================================================================
   PUREBANK CCFD — Main JavaScript
   ================================================================ */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initToasts();
    initNavbar();
    initNotificationBell();
    initAnimatedCounters();
    initPasswordStrength();
    initPredictionForm();
    initDatasetFeatures();
    initAboutTabs();
    initPageTransitions();
    initRippleButtons();
});

/* ----------------------------------------------------------------
   1. DARK / LIGHT THEME TOGGLE
   ---------------------------------------------------------------- */
function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;

    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);

    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateThemeIcon(next);
    });
}

function updateThemeIcon(theme) {
    const sunIcon = document.querySelector('.icon-sun');
    const moonIcon = document.querySelector('.icon-moon');
    if (!sunIcon || !moonIcon) return;

    if (theme === 'dark') {
        sunIcon.style.display = 'block';
        moonIcon.style.display = 'none';
    } else {
        sunIcon.style.display = 'none';
        moonIcon.style.display = 'block';
    }
}

/* ----------------------------------------------------------------
   2. TOAST NOTIFICATIONS (replace flash messages)
   ---------------------------------------------------------------- */
function initToasts() {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    container.querySelectorAll('.toast').forEach(toast => {
        // Animate in
        requestAnimationFrame(() => toast.classList.add('toast-show'));

        // Close button
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => dismissToast(toast));
        }

        // Auto dismiss
        const delay = parseInt(toast.dataset.autoDismiss) || 4000;
        setTimeout(() => dismissToast(toast), delay);
    });
}

function dismissToast(toast) {
    toast.classList.remove('toast-show');
    toast.classList.add('toast-hide');
    setTimeout(() => toast.remove(), 300);
}

/* ----------------------------------------------------------------
   3. NAVBAR TOGGLE (mobile hamburger)
   ---------------------------------------------------------------- */
function initNavbar() {
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');
    if (!hamburger || !navLinks) return;

    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navLinks.classList.toggle('open');
    });

    // Close menu when a link is clicked on mobile
    navLinks.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navLinks.classList.remove('open');
        });
    });

    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        const navbar = document.getElementById('navbar');
        if (navbar) {
            navbar.classList.toggle('navbar-scrolled', window.scrollY > 10);
        }
    });
}

/* ----------------------------------------------------------------
   4. NOTIFICATION BELL
   ---------------------------------------------------------------- */
function initNotificationBell() {
    const bell = document.getElementById('notifBell');
    const dropdown = document.getElementById('notifDropdown');
    const badge = document.getElementById('notifBadge');
    if (!bell || !dropdown) return;

    bell.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');

        if (dropdown.classList.contains('show') && dropdown.dataset.loaded !== 'true') {
            dropdown.innerHTML = '<div class="notif-loading">Loading...</div>';
            fetch('/api/notifications')
                .then(r => r.json())
                .then(data => {
                    dropdown.dataset.loaded = 'true';
                    if (!data || data.length === 0) {
                        dropdown.innerHTML = '<div class="notif-empty">No recent fraud alerts</div>';
                        return;
                    }
                    dropdown.innerHTML = '<div class="notif-title">Recent Fraud Alerts</div>' +
                        data.map(n =>
                            `<div class="notif-item">
                                <span class="notif-dot"></span>
                                <div>
                                    <strong>Acct ****${String(n.account).slice(-4)}</strong> &mdash; ${n.city}<br>
                                    <small>&#8377;${Number(n.amount).toLocaleString()} &middot; ${n.date}</small>
                                </div>
                            </div>`
                        ).join('');
                    if (badge) {
                        badge.textContent = data.length;
                        badge.style.display = 'flex';
                    }
                })
                .catch(() => {
                    dropdown.innerHTML = '<div class="notif-empty">Could not load notifications</div>';
                });
        }
    });

    document.addEventListener('click', () => dropdown.classList.remove('show'));
    dropdown.addEventListener('click', (e) => e.stopPropagation());
}

/* ----------------------------------------------------------------
   5. ANIMATED COUNTERS (Dashboard KPIs)
   ---------------------------------------------------------------- */
function initAnimatedCounters() {
    const counters = document.querySelectorAll('[data-count]');
    if (counters.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });

    counters.forEach(el => observer.observe(el));
}

function animateCounter(el) {
    const target = parseFloat(el.dataset.count);
    const isFloat = el.dataset.count.includes('.');
    const duration = 1500;
    const startTime = performance.now();

    function tick(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        const current = eased * target;

        let display = isFloat ? current.toFixed(2) : Math.floor(current).toLocaleString();
        if (el.dataset.prefix) display = el.dataset.prefix + display;
        if (el.dataset.suffix) display = display + el.dataset.suffix;
        el.textContent = display;

        if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

/* ----------------------------------------------------------------
   6. PASSWORD STRENGTH METER + TOGGLE
   ---------------------------------------------------------------- */
function initPasswordStrength() {
    const pwInput = document.getElementById('password');
    const meter = document.getElementById('pw-strength-meter');
    const label = document.getElementById('pw-strength-label');
    if (!pwInput) return;

    // Password toggle
    const toggle = document.getElementById('pw-toggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            const type = pwInput.type === 'password' ? 'text' : 'password';
            pwInput.type = type;
            toggle.innerHTML = type === 'password'
                ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>'
                : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
        });
    }

    // Strength meter
    if (!meter) return;
    pwInput.addEventListener('input', () => {
        const pw = pwInput.value;
        let score = 0;
        if (pw.length >= 8) score++;
        if (/[a-z]/.test(pw)) score++;
        if (/[A-Z]/.test(pw)) score++;
        if (/\d/.test(pw)) score++;
        if (/[@$!%*?&#]/.test(pw)) score++;

        const pct = (score / 5) * 100;
        meter.style.width = pct + '%';

        const levels = [
            { min: 0, color: '#ef4444', text: 'Very Weak' },
            { min: 20, color: '#f97316', text: 'Weak' },
            { min: 40, color: '#f59e0b', text: 'Fair' },
            { min: 60, color: '#84cc16', text: 'Good' },
            { min: 80, color: '#22c55e', text: 'Strong' },
        ];
        const level = [...levels].reverse().find(l => pct >= l.min);
        meter.style.background = level.color;
        if (label) {
            label.textContent = pw.length > 0 ? level.text : '';
            label.style.color = level.color;
        }
    });
}

/* ----------------------------------------------------------------
   7. PREDICTION — Multi-step wizard, gauge, auto-fill
   ---------------------------------------------------------------- */
function initPredictionForm() {
    const steps = document.querySelectorAll('.wizard-step');
    const indicators = document.querySelectorAll('.step-indicator');
    if (steps.length === 0) return;

    let currentStep = 0;

    window.nextStep = function() {
        const inputs = steps[currentStep].querySelectorAll('input, select');
        let valid = true;
        inputs.forEach(inp => {
            if (!inp.checkValidity()) {
                inp.reportValidity();
                valid = false;
            }
        });
        if (!valid) return;

        steps[currentStep].classList.remove('active');
        indicators[currentStep].classList.add('completed');
        currentStep++;
        steps[currentStep].classList.add('active');
        indicators[currentStep].classList.add('active');

        // Update review grid on last step
        if (currentStep === steps.length - 1) {
            updateReview();
        }
    };

    window.prevStep = function() {
        steps[currentStep].classList.remove('active');
        indicators[currentStep].classList.remove('active');
        currentStep--;
        steps[currentStep].classList.add('active');
        indicators[currentStep].classList.remove('completed');
    };

    function updateReview() {
        const set = (id, name) => {
            const el = document.getElementById(id);
            const inp = document.querySelector(`[name="${name}"]`);
            if (el && inp) el.textContent = inp.value || '--';
        };
        set('rev-type', 'transaction_type');
        set('rev-currency', 'currency_code');
        set('rev-country', 'transaction_country');
        set('rev-city', 'transaction_city');
        set('rev-amount', 'transaction_amount');
        set('rev-limit', 'credit_limit');
        set('rev-merchant', 'merchant_category_code');
        set('rev-otb', 'open_to_buy');
    }

    // Auto-fill demo data
    window.autoFillFraud = function() {
        fillForm({
            transaction_type: 'Cash Withdrawal',
            currency_code: 'INR',
            transaction_country: 'IN',
            transaction_city: 'Delhi',
            transaction_amount: '9500',
            credit_limit: '25000',
            merchant_category_code: '5411',
            open_to_buy: '2000'
        });
    };

    window.autoFillLegit = function() {
        fillForm({
            transaction_type: 'Online Payment',
            currency_code: 'INR',
            transaction_country: 'IN',
            transaction_city: 'Bangalore',
            transaction_amount: '1500',
            credit_limit: '150000',
            merchant_category_code: '5316',
            open_to_buy: '85000'
        });
    };

    function fillForm(data) {
        Object.entries(data).forEach(([name, value]) => {
            const el = document.querySelector(`[name="${name}"]`);
            if (el) { el.value = value; el.dispatchEvent(new Event('change')); }
        });
        // Jump to review step
        steps.forEach((s, i) => {
            s.classList.remove('active');
            if (indicators[i]) indicators[i].classList.add('completed');
        });
        currentStep = steps.length - 1;
        steps[currentStep].classList.add('active');
        if (indicators[currentStep]) indicators[currentStep].classList.add('active');
        updateReview();
    }

    // Gauge animation
    const gauge = document.getElementById('fraud-gauge');
    if (gauge) {
        const prob = parseFloat(gauge.dataset.probability);
        const circumference = 2 * Math.PI * 54; // ~339.29
        const offset = circumference - (prob / 100) * circumference;
        setTimeout(() => {
            const fill = gauge.querySelector('.gauge-fill');
            if (fill) fill.style.strokeDashoffset = offset;
        }, 300);
    }

    // Loading overlay on form submit
    const predictForm = document.getElementById('predict-form');
    if (predictForm) {
        predictForm.addEventListener('submit', () => {
            const overlay = document.getElementById('loadingOverlay');
            if (overlay) overlay.classList.add('active');
        });
    }
}

/* ----------------------------------------------------------------
   8. DATASET — Column sorting, search
   ---------------------------------------------------------------- */
function initDatasetFeatures() {
    const table = document.getElementById('dataset-table');
    if (!table) return;

    // Column sorting
    table.querySelectorAll('th.sortable').forEach(th => {
        th.style.cursor = 'pointer';
        th.dataset.order = 'none';
        th.addEventListener('click', () => {
            const index = parseInt(th.dataset.col);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const order = th.dataset.order === 'asc' ? 'desc' : 'asc';

            // Reset all headers
            table.querySelectorAll('th.sortable').forEach(h => {
                h.dataset.order = 'none';
                h.classList.remove('sort-asc', 'sort-desc');
            });
            th.dataset.order = order;
            th.classList.add(order === 'asc' ? 'sort-asc' : 'sort-desc');

            rows.sort((a, b) => {
                let va = a.children[index]?.textContent.trim() || '';
                let vb = b.children[index]?.textContent.trim() || '';
                const na = parseFloat(va), nb = parseFloat(vb);
                if (!isNaN(na) && !isNaN(nb)) {
                    return order === 'asc' ? na - nb : nb - na;
                }
                return order === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
            });

            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// Table search (global for inline onkeyup)
window.filterTable = function() {
    const filter = document.getElementById('search-bar').value.toLowerCase();
    document.querySelectorAll('#dataset-table tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(filter) ? '' : 'none';
    });
};

/* ----------------------------------------------------------------
   9. ABOUT PAGE — Tabs
   ---------------------------------------------------------------- */
function initAboutTabs() {
    const tabs = document.querySelectorAll('.about-tab-btn');
    const panels = document.querySelectorAll('.about-tab-panel');
    if (tabs.length === 0) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const target = document.getElementById(tab.dataset.tab);
            if (target) target.classList.add('active');
        });
    });
}

/* ----------------------------------------------------------------
   10. PAGE TRANSITIONS (fadeIn)
   ---------------------------------------------------------------- */
function initPageTransitions() {
    document.body.classList.add('page-loaded');

    // Hide loading overlay
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        setTimeout(() => overlay.classList.remove('active'), 100);
    }
}

/* ----------------------------------------------------------------
   11. RIPPLE BUTTONS
   ---------------------------------------------------------------- */
function initRippleButtons() {
    document.querySelectorAll('.btn-primary, .btn-full, .btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            const rect = this.getBoundingClientRect();
            ripple.style.left = (e.clientX - rect.left) + 'px';
            ripple.style.top = (e.clientY - rect.top) + 'px';
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
}
