// frontend/app.js – vanilla JavaScript for the Competition Platform SPA

// Elements
const competitionList = document.getElementById('competition-list');
const form = document.getElementById('new-competition-form');
const nameInput = document.getElementById('new-name');

// Helper to create a competition card
function createCard(comp) {
  const card = document.createElement('div');
  card.className = 'card';
  card.textContent = comp.name;
  return card;
}

// Render list
function renderCompetitions(comps) {
  competitionList.innerHTML = '';
  if (comps.length === 0) {
    competitionList.textContent = 'No competitions yet.';
    return;
  }
  comps.forEach(c => competitionList.appendChild(createCard(c)));
}

// Load competitions from API
async function loadCompetitions() {
  try {
    const token = localStorage.getItem('access_token');
    const resp = await fetch('/api/v1/competitions/', {
      headers: { 'Authorization': token ? `Bearer ${token}` : undefined },
    });
    if (!resp.ok) throw new Error('Failed to fetch competitions');
    const data = await resp.json();
    renderCompetitions(data);
  } catch (e) {
    console.error(e);
    competitionList.textContent = 'Error loading competitions.';
  }
}

// Submit new competition
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = nameInput.value.trim();
  if (!name) return;

  try {
    const token = localStorage.getItem('access_token');
    const resp = await fetch('/api/v1/competitions/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ name, category: document.getElementById('new-category').value }),
    });
    if (!resp.ok) throw new Error('Failed to create competition');
    const newComp = await resp.json();
    // prepend new competition to list
    const card = createCard(newComp);
    competitionList.insertBefore(card, competitionList.firstChild);
    nameInput.value = '';
  } catch (e) {
    console.error(e);
    alert('Could not create competition.');
  }
});

// Initial load
loadCompetitions();
