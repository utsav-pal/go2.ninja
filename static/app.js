// Go2.Ninja - Frontend JavaScript
// Minified and security-hardened for production

(function () {
    'use strict';

    // DOM Elements
    const form = document.getElementById('shorten-form');
    const input = document.getElementById('url-input');
    const btn = document.getElementById('shorten-btn');
    const btnText = btn?.querySelector('.btn-text');
    const btnLoader = btn?.querySelector('.btn-loader');
    const errorEl = document.getElementById('error-message');
    const resultEl = document.getElementById('result-section');
    const shortUrlEl = document.getElementById('short-url');
    const originalUrlEl = document.getElementById('original-url');
    const copyBtn = document.getElementById('copy-btn');
    const copyText = document.getElementById('copy-text');
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.querySelector('.nav-links');

    // Mobile nav
    navToggle?.addEventListener('click', () => navLinks?.classList.toggle('active'));
    navLinks?.querySelectorAll('.nav-link').forEach(link =>
        link.addEventListener('click', () => navLinks?.classList.remove('active'))
    );

    // FAQ Accordion
    document.querySelectorAll('.faq-question').forEach(btn => {
        btn.addEventListener('click', () => {
            const item = btn.parentElement;
            const wasActive = item.classList.contains('active');
            document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));
            if (!wasActive) item.classList.add('active');
        });
    });

    // URL normalization
    function normalizeUrl(url) {
        url = url.trim();
        if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
        return url;
    }

    // URL validation
    function isValidUrl(str) {
        try {
            const url = new URL(str);
            return ['http:', 'https:'].includes(url.protocol);
        } catch { return false; }
    }

    // Escape HTML (XSS prevention)
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Show/hide helpers
    function showError(msg) {
        if (errorEl) {
            errorEl.textContent = msg;
            errorEl.classList.remove('hidden');
        }
    }

    function hideError() {
        errorEl?.classList.add('hidden');
    }

    function setLoading(loading) {
        if (btn) btn.disabled = loading;
        btnText?.classList.toggle('hidden', loading);
        btnLoader?.classList.toggle('hidden', !loading);
        btn?.querySelector('.btn-arrow')?.classList.toggle('hidden', loading);
    }

    function showResult(data) {
        if (shortUrlEl) shortUrlEl.value = data.short_url;
        if (originalUrlEl) originalUrlEl.textContent = data.original_url.length > 50
            ? data.original_url.slice(0, 50) + '...'
            : data.original_url;
        resultEl?.classList.remove('hidden');
        copyBtn?.classList.remove('copied');
        if (copyText) copyText.textContent = 'Copy';
    }

    // Form submit
    form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        let url = input?.value?.trim() || '';
        if (!url) return showError('Please enter a URL');

        url = normalizeUrl(url);
        if (input) input.value = url;

        if (!isValidUrl(url)) return showError('Please enter a valid URL');

        setLoading(true);

        try {
            const res = await fetch('/api/shorten', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Failed to shorten URL');

            showResult(data);
        } catch (err) {
            showError(err.message || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    });

    // Copy to clipboard
    copyBtn?.addEventListener('click', async () => {
        const url = shortUrlEl?.value;
        if (!url) return;

        try {
            await navigator.clipboard.writeText(url);
        } catch {
            shortUrlEl?.select();
            document.execCommand('copy');
        }

        copyBtn.classList.add('copied');
        if (copyText) copyText.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.classList.remove('copied');
            if (copyText) copyText.textContent = 'Copy';
        }, 2000);
    });

    // Clear on input
    input?.addEventListener('input', () => {
        resultEl?.classList.add('hidden');
        hideError();
    });

    // Smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', (e) => {
            const href = a.getAttribute('href');
            if (href === '#') return;
            e.preventDefault();
            document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });
        });
    });
})();
