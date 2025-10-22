let allAnnonces = [];
document.addEventListener('DOMContentLoaded', async () => { await loadData(); });
async function loadData() { const r = await fetch('data.json'); allAnnonces = await r.json(); }