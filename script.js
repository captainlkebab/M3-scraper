const folderPath = './';  // Angenommen, die JSON-Datei liegt im gleichen Ordner wie die HTML-Datei
const today = new Date();
const year = today.getFullYear().toString().slice(-2);  // Holt die letzten zwei Ziffern des Jahres (z.B. "25" für 2025)
const month = String(today.getMonth() + 1).padStart(2, '0');  // Holt den Monat (01-12)
const day = String(today.getDate()).padStart(2, '0');  // Holt den Tag (01-31)
const fileName = `Refurbed_${year}${month}${day}.json`;  // Erzeugt den Dateinamen im Format "Refurbed_YYMMDD.json"


let data = [];

fetch(`${folderPath}${fileName}`)
  .then(response => {
    if (!response.ok) throw new Error('Data not found for today');
    return response.json();
  })
  .then(json => {
    data = json;
    renderResults(data);
  })
  .catch(err => {
    document.getElementById('results').innerHTML = `<p>Error loading data: ${err.message}</p>`;
  });

document.getElementById('search').addEventListener('input', (e) => {
  const q = e.target.value.toLowerCase();
  const filtered = data.filter(item =>
    item.title.toLowerCase().includes(q) ||
    item.brand?.toLowerCase().includes(q) ||
    item.model?.toLowerCase().includes(q)
  );
  renderResults(filtered);
});

function renderResults(products) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';

  if (products.length === 0) {
    resultsDiv.innerHTML = '<p>No products found.</p>';
    return;
  }

  products.forEach(p => {
    const div = document.createElement('div');
    div.className = 'product';
    div.innerHTML = `
      <h3>${p.title}</h3>
      <p><strong>Brand:</strong> ${p.brand || '-'} | <strong>Model:</strong> ${p.model || '-'}</p>
      <p><strong>Grade:</strong> ${p.grade || '-'} | <strong>Refurbished:</strong> ${p.refurbished ? 'Yes' : 'No'}</p>
      <p><strong>Price:</strong> ${p.price} ${p.currency_iso}</p>
      <p><a href="${p.url}" target="_blank">Buy now</a> — <small>Source: ${p.source}</small></p>
    `;
    resultsDiv.appendChild(div);
  });
}
