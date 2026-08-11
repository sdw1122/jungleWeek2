let chosen = null;
let positive = 0;
let negative = 0;
let completionShown = false;
let csrf = '';
const messages = document.querySelector('#messages');
const stagePlant = document.querySelector('#seed');
const seedActions = document.querySelector('#seed-actions');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const actionButtons = document.querySelectorAll('[data-action]');
const prefixPattern = /^(사랑을 담은|행운의|감사의|건강을 기원하는|싱그러운|우리의|존경의|사랑의)\s*/;

const stages = [
  { min: 0, name: '씨앗', emoji: '🌰', next: 5, mood: '아직 싹을 틔우기 전입니다. 정성껏 돌봐주세요!' },
  { min: 5, name: '떡잎', emoji: '🌱', next: 20, mood: '작은 떡잎이 고개를 내밀었어요.' },
  { min: 20, name: '본잎', emoji: '🪴', next: 40, mood: '튼튼한 본잎이 자라며 생기가 넘쳐요.' },
  { min: 40, name: '봉오리', emoji: '🌷', next: 70, mood: '곧 꽃을 피울 봉오리가 맺혔어요.' },
  { min: 70, name: '꽃', emoji: '🌸', next: 100, mood: '정성 덕분에 아름다운 꽃이 피었어요!' }
];
const replies = {
  water: '시원해요! 뿌리가 촉촉해졌어요. 💧',
  sun: '따뜻한 햇빛 덕분에 힘이 나요! ☀️',
  pet: '정성스러운 손길이 느껴져요. 🌱',
  ignore: '조금 외로워요. 저를 잊지 말아주세요. 🌧️'
};
const apiActions = { water: 'WATER', sun: 'SUNLIGHT', pet: 'PET', ignore: 'IGNORE' };

async function loadCsrf() {
  const response = await fetch('/api/v1/auth/csrf', { credentials: 'same-origin' });
  const payload = await response.json();
  if (!response.ok) throw new Error('보안 정보를 불러오지 못했습니다.');
  csrf = payload.data.csrfToken;
}

async function apiRequest(path, options = {}) {
  if (options.method === 'POST' && !csrf) await loadCsrf();
  const response = await fetch(path, {
    ...options,
    credentials: 'same-origin',
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(options.method === 'POST' ? { 'X-CSRF-Token': csrf } : {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (response.status === 401) {
    location.href = `/login.html?next=${encodeURIComponent(location.pathname + location.search)}`;
    throw new Error('로그인이 필요합니다.');
  }
  if (!response.ok) throw new Error(payload.error?.message || '요청 처리에 실패했습니다.');
  return payload;
}

function renderGrowth(animate = false) {
  if (!chosen) return;
  positive = chosen.positiveEnergy;
  negative = chosen.negativeEnergy;
  const total = chosen.growthScore;
  const stage = [...stages].reverse().find(item => total >= item.min);
  const plantName = chosen.name.replace(prefixPattern, '');
  document.querySelector('#plant-name').textContent = plantName;
  document.querySelector('.plant-chip h2').textContent = plantName;
  document.querySelector('#positive').textContent = positive;
  document.querySelector('#negative').textContent = negative;
  document.querySelector('#total').textContent = total;
  document.querySelector('#positive-bar').style.width = `${Math.min(100, positive)}%`;
  document.querySelector('#negative-bar').style.width = `${Math.min(100, negative)}%`;
  document.querySelector('#total-bar').style.width = `${total}%`;
  document.querySelector('#next').textContent = total >= 100 ? '완료' : Math.max(0, stage.next - total);
  document.querySelector('#stage-label').textContent = `${stage.name} 단계`;
  document.querySelector('#mini-stage').textContent = stage.emoji;
  document.querySelector('#mood-copy').textContent = chosen.mood === 'NEGATIVE'
    ? '관심이 조금 부족해요. 따뜻하게 돌봐주세요.'
    : stage.mood;
  seedActions.hidden = total >= 5;
  chatForm.hidden = total < 5;
  if (stagePlant.textContent !== stage.emoji) {
    stagePlant.textContent = stage.emoji;
    if (animate) {
      stagePlant.animate(
        [{ transform: 'scale(.5) rotate(-12deg)', opacity: .2 }, { transform: 'scale(1.2) rotate(5deg)', opacity: 1 }, { transform: 'scale(1)' }],
        { duration: 600, easing: 'ease-out' }
      );
    }
  }
}

function showCompletion() {
  if (chosen?.growthScore >= 100 && !completionShown) {
    completionShown = true;
    window.setTimeout(() => {
      document.querySelector('#growth-modal').hidden = false;
      document.body.style.overflow = 'hidden';
    }, 500);
  }
}

async function care(actionType, note = null, sentiment = 'POSITIVE') {
  const payload = await apiRequest(`/api/v1/plants/${chosen.id}/care`, {
    method: 'POST',
    body: JSON.stringify({ actionType, note, sentiment })
  });
  chosen = payload.data.plant;
  renderGrowth(true);
  showCompletion();
}

actionButtons.forEach(button => button.addEventListener('click', async () => {
  if (!chosen || button.disabled) return;
  actionButtons.forEach(item => { item.disabled = true; });
  const action = button.dataset.action;
  try {
    await care(apiActions[action]);
    messages.insertAdjacentHTML('beforeend', `<p class="user">${replies[action]}</p>`);
    messages.scrollTop = messages.scrollHeight;
    stagePlant.animate(
      [{ transform: 'scale(.94)' }, { transform: 'scale(1.08)' }, { transform: 'scale(1)' }],
      { duration: 320 }
    );
  } catch (error) {
    messages.insertAdjacentHTML('beforeend', `<p>${error.message}</p>`);
  } finally {
    actionButtons.forEach(item => { item.disabled = false; });
  }
}));

const positiveWords = ['사랑', '예뻐', '예쁘다', '좋아', '고마워', '잘했어', '힘내', '행복', '멋져', '소중'];
const negativeWords = ['싫어', '미워', '못생겼', '바보', '짜증', '죽어', '별로', '안 예뻐'];
chatForm.addEventListener('submit', async event => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text || !chosen || chatInput.disabled) return;
  const isNegative = negativeWords.some(word => text.includes(word));
  const isPositive = positiveWords.some(word => text.includes(word));
  const escaped = text.replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  chatInput.disabled = true;
  try {
    await care('PRAISE', text, isNegative && !isPositive ? 'NEGATIVE' : 'POSITIVE');
    messages.insertAdjacentHTML('beforeend', `<p class="user">${escaped}</p>`);
    messages.insertAdjacentHTML('beforeend', `<p>${isNegative && !isPositive ? '조금 속상해요. 그래도 곁에 있어주세요. 🌧️' : '따뜻한 말 고마워요! 마음이 쑥쑥 자라요. 🌱'}</p>`);
    chatInput.value = '';
    messages.scrollTop = messages.scrollHeight;
  } catch (error) {
    messages.insertAdjacentHTML('beforeend', `<p>${error.message}</p>`);
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});

async function loadPlant() {
  try {
    const requestedId = Number(new URLSearchParams(location.search).get('plantId'));
    if (Number.isInteger(requestedId) && requestedId > 0) {
      const payload = await apiRequest(`/api/v1/plants/${requestedId}`);
      chosen = payload.data.plant;
    } else {
      const payload = await apiRequest('/api/v1/plants');
      if (!payload.data.plants.length) {
        location.href = 'plant-select.html';
        return;
      }
      chosen = payload.data.plants[0];
      history.replaceState({}, '', `dashboard-v2.html?plantId=${chosen.id}`);
    }
    renderGrowth(false);
  } catch (error) {
    messages.innerHTML = `<p>${error.message}</p>`;
  }
}

const profileToggle = document.querySelector('#profile-toggle');
const profileCard = document.querySelector('#profile-card');
profileToggle.addEventListener('click', () => {
  const willOpen = profileCard.hidden;
  profileCard.hidden = !willOpen;
  profileToggle.setAttribute('aria-expanded', String(willOpen));
});
document.addEventListener('click', event => {
  if (!profileCard.hidden && !profileCard.contains(event.target) && event.target !== profileToggle) {
    profileCard.hidden = true;
    profileToggle.setAttribute('aria-expanded', 'false');
  }
});
document.querySelector('#profile-logout').addEventListener('click', async () => {
  try {
    await apiRequest('/api/v1/auth/logout', { method: 'POST' });
    location.href = '/login.html';
  } catch (error) {
    messages.insertAdjacentHTML('beforeend', `<p>${error.message}</p>`);
  }
});

const growthModal = document.querySelector('#growth-modal');
function closeGrowthModal() {
  growthModal.hidden = true;
  document.body.style.overflow = '';
}
document.querySelector('.modal-later').addEventListener('click', closeGrowthModal);
document.querySelector('.growth-modal-backdrop').addEventListener('click', closeGrowthModal);
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !growthModal.hidden) closeGrowthModal();
});

loadPlant();
