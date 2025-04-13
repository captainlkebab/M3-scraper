const folderPath = 'github/Scraped/';
const today = new Date().toISOString().slice(0, 10);  // z.B. "2025-04-12"
const fileName = `Refurbed_${today}.json`;

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
