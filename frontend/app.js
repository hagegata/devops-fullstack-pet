const form = document.getElementById('shorten-form');
const urlInput = document.getElementById('url-input');
const resultDiv = document.getElementById('result');
const shortLink = document.getElementById('short-link');
const errorDiv = document.getElementById('error');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    resultDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');

    const url = urlInput.value.trim();
    if (!url) return;

    try {
        const response = await fetch('/api/shorten', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const fullShortUrl = `${window.location.origin}/api/${data.short}`;
        shortLink.href = fullShortUrl;
        shortLink.textContent = fullShortUrl;
        resultDiv.classList.remove('hidden');
        urlInput.value = '';
    } catch (err) {
        errorDiv.textContent = `Ошибка: ${err.message}`;
        errorDiv.classList.remove('hidden');
    }
});
