const cards = [...document.querySelectorAll('.plant-card')];
const filters = document.querySelectorAll('.filter');
const search = document.querySelector('#search');
const bar = document.querySelector('.selection-bar');
const selectedName = document.querySelector('#selected-name');
const continueButton = document.querySelector('#continue');
let category = 'all';
let selected = null;

cards.forEach(card => {
  card.querySelector('.photo').style.backgroundImage = `url("${card.dataset.image}")`;
});

function filterCards() {
  const term = search.value.trim().toLowerCase();
  let count = 0;
  cards.forEach(card => {
    const visible = (category === 'all' || card.dataset.category === category)
      && card.dataset.name.toLowerCase().includes(term);
    card.hidden = !visible;
    if (visible) count += 1;
  });
  document.querySelector('.empty').hidden = count > 0;
}

async function csrfToken() {
  const response = await fetch('/api/v1/auth/csrf', { credentials: 'same-origin' });
  const payload = await response.json();
  if (!response.ok) throw new Error('보안 정보를 불러오지 못했습니다.');
  return payload.data.csrfToken;
}

filters.forEach(button => button.addEventListener('click', () => {
  category = button.dataset.filter;
  filters.forEach(item => item.classList.toggle('active', item === button));
  filterCards();
}));
search.addEventListener('input', filterCards);

cards.forEach(card => card.querySelector('button').addEventListener('click', () => {
  cards.forEach(item => item.classList.toggle('selected', item === card));
  selected = card;
  selectedName.textContent = card.dataset.name;
  bar.hidden = false;
}));

continueButton.addEventListener('click', async () => {
  if (!selected || continueButton.disabled) return;
  continueButton.disabled = true;
  continueButton.textContent = '식물을 저장하는 중…';
  try {
    const token = await csrfToken();
    const response = await fetch('/api/v1/plants', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token
      },
      body: JSON.stringify({
        name: selected.dataset.name,
        imageUrl: selected.dataset.image
      })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error?.message || '식물을 저장하지 못했습니다.');
    }
    document.body.classList.add('page-leave');
    window.setTimeout(() => {
      location.href = `dashboard-v2.html?plantId=${payload.data.plant.id}`;
    }, 320);
  } catch (error) {
    window.alert(error.message);
    continueButton.disabled = false;
    continueButton.innerHTML = '이 식물 키우기 <span>→</span>';
  }
});

document.querySelector('.close').addEventListener('click', () => {
  location.href = 'welcome.html';
});
