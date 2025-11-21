document.addEventListener('DOMContentLoaded', () => {
  loadSectors();
  setupModal();
  document.getElementById('interest-form').addEventListener('submit', onSearchSubmit);
});

function loadSectors() {
  const sectorContainer = document.getElementById('sector-grid-container');
  fetch('/sectors')
    .then(r => {
      if (!r.ok) throw new Error('sectors fetch failed');
      return r.json();
    })
    .then(sectorNames => {
      sectorContainer.innerHTML = '';
      sectorNames.forEach(name => {
        const label = document.createElement('label');
        label.className = 'sector-pill';
        label.innerHTML = `<input type="checkbox" name="sector" value="${escapeHtml(name)}"> <span>${escapeHtml(name)}</span>`;
        sectorContainer.appendChild(label);
      });
    })
    .catch(err => {
      console.error('Error loading sectors:', err);
      sectorContainer.innerHTML = '<p class="error">Could not load sectors.</p>';
    });
}

function onSearchSubmit(event) {
  event.preventDefault();
  const checkedBoxes = document.querySelectorAll('input[name="sector"]:checked');
  const selectedSectors = Array.from(checkedBoxes).map(cb => cb.value);
  const location = document.getElementById('location-input').value;
  const resultsContainer = document.getElementById('results-container');
  resultsContainer.innerHTML = '<p class="muted">Searching for centres...</p>';

  if (selectedSectors.length === 0) {
    resultsContainer.innerHTML = '<p class="error">Please select at least one sector.</p>';
    return;
  }

  fetch('/match', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sectors: selectedSectors, location }),
  })
    .then(r => r.json())
    .then(data => {
      renderResults(data || []);
    })
    .catch(err => {
      console.error('Error:', err);
      resultsContainer.innerHTML = '<p class="error">An error occurred.</p>';
    });
}

function renderResults(data) {
  const resultsContainer = document.getElementById('results-container');
  resultsContainer.innerHTML = '';

  if (!Array.isArray(data) || data.length === 0) {
    resultsContainer.innerHTML = '<p class="muted">No matching centres found.</p>';
    return;
  }

  data.forEach(c => {
    const card = document.createElement('div');
    card.className = 'result-card';

    const coursesHTML = (c.offered_courses || []).map(courseName =>
      `<a href="#" class="offered-course-link" data-career-name="${escapeHtml(courseName)}">${escapeHtml(courseName)}</a>`
    ).join(', ');

    card.innerHTML = `
      <h3 class="centre-name">${escapeHtml(c.centre_name)}</h3>
      <div class="centre-meta">
        <div><strong>Address:</strong> ${escapeHtml(c.address || 'Not available')}</div>
        <div><strong>Contact:</strong> ${escapeHtml(c.contact || 'Not available')}</div>
        <div><strong>Courses:</strong> ${coursesHTML || '—'}</div>
        <div class="card-links">
          ${c.source_url ? `<a class="btn-link" href="${escapeAttr(c.source_url)}" target="_blank">Source</a>` : ''}
        </div>
      </div>
    `;

    resultsContainer.appendChild(card);
  });
}

// --- Modal handling ---
function setupModal() {
  const modal = document.getElementById('career-modal');
  const closeBtn = document.getElementById('modal-close-btn');
  const okBtn = document.getElementById('modal-ok');
  const resultsContainer = document.getElementById('results-container');

  resultsContainer.addEventListener('click', e => {
    if (e.target.classList.contains('offered-course-link')) {
      e.preventDefault();
      const careerName = e.target.dataset.careerName;
      openCareerModal(careerName);
    }
  });

  closeBtn.addEventListener('click', () => hideModal());
  okBtn.addEventListener('click', () => hideModal());
  window.addEventListener('keydown', ev => { if (ev.key === 'Escape') hideModal(); });

  function hideModal() {
    modal.style.opacity = 0;
    modal.style.pointerEvents = 'none';
    modal.setAttribute('aria-hidden', 'true');
  }
}

function openCareerModal(careerName) {
  const modal = document.getElementById('career-modal');
  const titleEl = document.getElementById('modal-career-name');
  const attrsEl = document.getElementById('modal-attributes');
  const learningsEl = document.getElementById('modal-key-learnings');
  const sectorEl = document.getElementById('modal-sector');
  const sourceLink = document.getElementById('modal-source-link');

  titleEl.textContent = 'Loading...';
  attrsEl.textContent = '';
  learningsEl.innerHTML = '';
  sectorEl.textContent = '';

  fetch(`/career/${encodeURIComponent(careerName)}`)
    .then(r => {
      if (!r.ok) throw new Error('career fetch failed');
      return r.json();
    })
    .then(data => {
      titleEl.textContent = data.name || careerName;
      sectorEl.textContent = data.sector ? `Sector: ${data.sector}` : '';
      attrsEl.textContent = data.attributes || 'Not available.';
      learningsEl.innerHTML = '';

      if (Array.isArray(data.key_learnings) && data.key_learnings.length) {
        data.key_learnings.forEach(k => {
          const li = document.createElement('li'); li.textContent = k; learningsEl.appendChild(li);
        });
      } else {
        learningsEl.innerHTML = '<li>Not available.</li>';
      }

      // optional source link
      sourceLink.href = data.source_url || '#';
      sourceLink.style.display = data.source_url ? 'inline-block' : 'none';

      // show modal
      modal.style.pointerEvents = 'auto';
      modal.style.opacity = 1;
      modal.setAttribute('aria-hidden', 'false');
    })
    .catch(err => {
      console.error('Error fetching career details:', err);
      titleEl.textContent = careerName;
      attrsEl.textContent = 'Could not load details.';
      learningsEl.innerHTML = '<li>Not available.</li>';
      modal.style.pointerEvents = 'auto';
      modal.style.opacity = 1;
      modal.setAttribute('aria-hidden', 'false');
    });
}

// small helpers
function escapeHtml(s) {
  if (!s && s !== 0) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function escapeAttr(s) {
  return escapeHtml(s).replace(/"/g, '&quot;');
}
