let allAnnonces = [];

document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    setupFilters();
    filterAndDisplay();
    updateStats();
});

async function loadData() {
    try {
        const response = await fetch('data.json');
        allAnnonces = await response.json();
    } catch (error) {
        console.error('Erreur: Impossible de charger les données', error);
        allAnnonces = [];
    }
}

function setupFilters() {
    document.getElementById('filter-loyer').addEventListener('change', filterAndDisplay);
    document.getElementById('filter-pieces').addEventListener('change', filterAndDisplay);
    document.getElementById('filter-meuble').addEventListener('change', filterAndDisplay);
    document.getElementById('search').addEventListener('input', filterAndDisplay);
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    document.getElementById('export-csv').addEventListener('click', exportCSV);
    document.getElementById('export-json').addEventListener('click', exportJSON);
}

function filterAndDisplay() {
    const loyerFilter = document.getElementById('filter-loyer').value;
    const piecesFilter = document.getElementById('filter-pieces').value;
    const meubleFilter = document.getElementById('filter-meuble').value;
    const searchTerm = document.getElementById('search').value.toLowerCase();
    let filtered = allAnnonces.filter(ann => {
        let match = true;
        if (loyerFilter) {
            const [min, max] = loyerFilter.split('-').map(Number);
            const loyer = Number(ann.Loyer);
            match = match && loyer >= min && loyer <= max;
        }
        if (piecesFilter) {
            match = match && Number(ann.Pièces) == Number(piecesFilter);
        }
        if (meubleFilter) {
            match = match && ann.Meublé === meubleFilter;
        }
        if (searchTerm) {
            const searchText = `${ann.Adresse} ${ann['Description courte']}`.toLowerCase();
            match = match && searchText.includes(searchTerm);
        }
        return match;
    });

    displayTable(filtered);
    document.getElementById('count').textContent = filtered.length;
}

function displayTable(annonces) {
    const tbody = document.getElementById('annonces-tbody');
    tbody.innerHTML = '';

    if (annonces.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center">Aucune annonce ne correspond à vos critères</td></tr>';
        return;
    }

    annonces.forEach(ann => {
        const row = `
            <tr>
                <td><strong>CHF ${Number(ann.Loyer).toLocaleString()}</strong></td>
                <td>${ann.Pièces}p</td>
                <td>${ann.Surface}m²</td>
                <td>${ann.Adresse}</td>
                <td>${ann['Description courte']}</td>
                <td><a href="${ann['URL annonce']}" target="_blank">Voir 🔗</a></td>
                <td>${ann.Portail}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

function resetFilters() {
    document.getElementById('filter-loyer').value = '';
    document.getElementById('filter-pieces').value = '';
    document.getElementById('filter-meuble').value = '';
    document.getElementById('search').value = '';
    filterAndDisplay();
}

function updateStats() {
    if (allAnnonces.length === 0) return;

    const loyers = allAnnonces.map(a => Number(a.Loyer));
    const surfaces = allAnnonces.map(a => Number(a.Surface));
    const avgLoyer = Math.round(loyers.reduce((a, b) => a + b, 0) / loyers.length);
    const avgSurface = Math.round(surfaces.reduce((a, b) => a + b, 0) / surfaces.length * 10) / 10;
    const bestDeal = Math.min(...allAnnonces.map(a => Number(a.Loyer) / Number(a.Surface)));
    const portals = new Set(allAnnonces.map(a => a.Portail)).size;

    document.getElementById('stat-avg-loyer').textContent = `CHF ${avgLoyer.toLocaleString()}`;
    document.getElementById('stat-avg-surface').textContent = `${avgSurface}m²`;
    document.getElementById('stat-best-deal').textContent = `CHF ${bestDeal.toFixed(1)}/m²`;
    document.getElementById('stat-portals').textContent = `${portals} sources`;
}

function exportCSV() {
    if (allAnnonces.length === 0) {
        alert('Aucune donnée à exporter');
        return;
    }
    const headers = Object.keys(allAnnonces[0]);
    let csv = headers.join(',') + '\n';
    allAnnonces.forEach(ann => {
        const row = headers.map(h => JSON.stringify(ann[h] || '')).join(',');
        csv += row + '\n';
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `annonces-export-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
}

function exportJSON() {
    if (allAnnonces.length === 0) {
        alert('Aucune donnée à exporter');
        return;
    }
    const blob = new Blob([JSON.stringify(allAnnonces, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `annonces-export-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}
