let chosen = null;
let completionShown = false;
let csrf = '';
let lastAiEmotion = null;

const messages = document.querySelector('#messages');
const stagePlant = document.querySelector('#seed');
const seedActions = document.querySelector('#seed-actions');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const actionButtons = document.querySelectorAll('[data-action]');
const prefixPattern = /^(사랑을 담은|행운의|감사의|건강을 기원하는|싱그러운|우리의|존경의|사랑의)\s*/;
const seedStyles = {
  '몬스테라': 'monstera', '스투키': 'stucky', '산세베리아': 'sansevieria',
  '스킨답서스': 'pothos', '아레카야자': 'areca', '파키라': 'pachira',
  '고무나무': 'rubber', '스파티필름': 'peace-lily', '아이비': 'ivy',
  '필로덴드론': 'philodendron', '테이블야자': 'parlor-palm', '알로에': 'aloe',
  '선인장': 'cactus', '페페로미아': 'peperomia', '행운목': 'lucky-bamboo',
  '벤자민고무나무': 'ficus', '칼라데아': 'calathea', '드라세나': 'dracaena',
  '호야': 'hoya', '아디안텀': 'maidenhair'
};
const stageStyles = { '씨앗': 'seed', '떡잎': 'sprout', '본잎': 'leaf', '봉오리': 'bud', '꽃': 'mature' };

function plantModelMarkup() {
  return '<span class="plant-model"><span class="plant-trunk"></span><span class="plant-pot"></span>'
    + Array.from({ length: 8 }, (_, index) => `<i class="plant-leaf leaf-${index + 1}"></i>`).join('')
    + '<i class="plant-bud"></i>'
    + Array.from({ length: 5 }, (_, index) => `<i class="plant-bloom bloom-${index + 1}"></i>`).join('')
    + '</span>';
}

function applyGrowthVisual(element, seedStyle, stageStyle, isNegative) {
  const baseClass = element.id === 'mini-stage' ? 'mini-seed' : 'stage-plant';
  element.className = baseClass;
  element.classList.add('species-growth', `seed-${seedStyle}`, `growth-${stageStyle}`);
  if (stageStyle === 'seed') {
    element.classList.add('species-seed');
    element.replaceChildren();
  } else {
    element.classList.add('has-model');
    element.innerHTML = plantModelMarkup();
  }
  if (isNegative) element.classList.add('is-wilted');
}

const stages = [
  { min: 0, name: '씨앗', emoji: '🌰', next: 5, mood: '아직 싹을 틔우기 전입니다. 정성껏 돌봐주세요!' },
  { min: 5, name: '떡잎', emoji: '🌱', next: 20, mood: '작은 떡잎이 고개를 내밀었어요.' },
  { min: 20, name: '본잎', emoji: '🪴', next: 40, mood: '튼튼한 본잎이 자라며 생기가 넘쳐요.' },
  { min: 40, name: '봉오리', emoji: '🌷', next: 70, mood: '곧 꽃을 피울 봉오리가 맺혔어요.' },
  { min: 70, name: '꽃', emoji: '🌸', next: 100, mood: '정성 덕분에 아름다운 꽃이 피었어요!' }
];
const replies = {
  water: '시원해요!<br>뿌리가 축축해졌어요!',
  sun: '따뜻한 햇빛 덕분에 힘이 나요! ☀️',
  pet: '정성스러운 손길이 느껴져요. 🌱',
  ignore: '조금 외로워요. 저를 잊지 말아주세요. 🌧️'
};
const apiActions = { water: 'WATER', sun: 'SUNLIGHT', pet: 'PET', ignore: 'IGNORE' };

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
}

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
  const total = chosen.growthScore;
  const stage = [...stages].reverse().find(item => total >= item.min);
  const plantName = chosen.name.replace(prefixPattern, '');
  const isNegative = chosen.negativeEnergy > chosen.positiveEnergy;
  const seedStyle = seedStyles[plantName] || 'monstera';
  const stageStyle = stageStyles[stage.name];
  const visualKey = `${seedStyle}-${stageStyle}-${isNegative ? 'wilted' : 'healthy'}`;

  document.querySelector('#plant-name').textContent = plantName;
  document.querySelector('.plant-chip h2').textContent = plantName;
  document.querySelector('#positive').textContent = chosen.positiveEnergy;
  document.querySelector('#negative').textContent = chosen.negativeEnergy;
  document.querySelector('#total').textContent = total;
  document.querySelector('#positive-bar').style.width = `${Math.min(100, chosen.positiveEnergy)}%`;
  document.querySelector('#negative-bar').style.width = `${Math.min(100, chosen.negativeEnergy)}%`;
  document.querySelector('#total-bar').style.width = `${total}%`;
  document.querySelector('#next').textContent = total >= 100 ? '완료' : Math.max(0, stage.next - total);
  document.querySelector('#stage-label').textContent = `${isNegative ? `흑화(${stage.name})` : stage.name} 단계`;
  const miniStage = document.querySelector('#mini-stage');
  applyGrowthVisual(miniStage, seedStyle, stageStyle, isNegative);
  document.querySelector('#mood-copy').textContent = lastAiEmotion
    ? `현재 기분: ${lastAiEmotion}`
    : (isNegative ? '관심이 조금 부족해요. 따뜻하게 돌봐주세요.' : stage.mood);

  seedActions.hidden = total >= 5;
  chatForm.hidden = total < 5;
  if (stagePlant.dataset.visual !== visualKey) {
    stagePlant.dataset.visual = visualKey;
    applyGrowthVisual(stagePlant, seedStyle, stageStyle, isNegative);
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
  lastAiEmotion = null;
  renderGrowth(true);
  showCompletion();
}

actionButtons.forEach(button => button.addEventListener('click', async () => {
  if (!chosen || button.disabled) return;
  actionButtons.forEach(item => { item.disabled = true; });
  const action = button.dataset.action;
  try {
    await care(apiActions[action]);
    const replyClass = action === 'water' ? 'narration' : 'user';
    messages.insertAdjacentHTML('beforeend', `<p class="${replyClass}">${replies[action]}</p>`);
    messages.scrollTop = messages.scrollHeight;
    stagePlant.animate(
      [{ transform: 'scale(.94)' }, { transform: 'scale(1.08)' }, { transform: 'scale(1)' }],
      { duration: 320 }
    );
  } catch (error) {
    messages.insertAdjacentHTML('beforeend', `<p>${escapeHtml(error.message)}</p>`);
  } finally {
    actionButtons.forEach(item => { item.disabled = false; });
  }
}));

chatForm.addEventListener('submit', async event => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text || !chosen || chatInput.disabled || chosen.growthScore >= 100) return;

  messages.insertAdjacentHTML('beforeend', `<p class="user">${escapeHtml(text)}</p>`);
  chatInput.value = '';
  chatInput.disabled = true;
  messages.scrollTop = messages.scrollHeight;

  try {
    const payload = await apiRequest('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ plant_id: chosen.id, message: text })
    });
    chosen = payload.plant;
    lastAiEmotion = payload.emotion || null;
    messages.insertAdjacentHTML('beforeend', `<p>${escapeHtml(payload.response)}</p>`);
    renderGrowth(true);
    showCompletion();
  } catch (error) {
    messages.insertAdjacentHTML('beforeend', `<p>${escapeHtml(error.message)}</p>`);
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
    messages.scrollTop = messages.scrollHeight;
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
    messages.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
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
    messages.insertAdjacentHTML('beforeend', `<p>${escapeHtml(error.message)}</p>`);
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

const giftForm = document.querySelector('#gift-form');
const giftNickname = document.querySelector('#gift-nickname');
const giftMessage = document.querySelector('#gift-message');
const giftMessageCount = document.querySelector('#gift-message-count');
const giftError = document.querySelector('#gift-error');
giftMessage.addEventListener('input', () => {
  giftMessageCount.textContent = giftMessage.value.length;
});
giftNickname.addEventListener('input', () => {
  giftError.textContent = '';
});
giftForm.addEventListener('submit', event => {
  event.preventDefault();
  const nickname = giftNickname.value.trim();
  const message = giftMessage.value.trim();
  if (nickname.length < 2) {
    giftError.textContent = '닉네임을 2자 이상 입력해주세요.';
    giftNickname.focus();
    return;
  }
  const submitButton = giftForm.querySelector('.gift-submit');
  submitButton.disabled = true;
  submitButton.querySelector('b').textContent = '선물 카드를 만드는 중…';
  window.setTimeout(() => {
    document.querySelector('#gift-recipient').textContent = nickname;
    document.querySelector('#gift-plant-name').textContent = chosen?.name || '식물';
    document.querySelector('#gift-plant-icon').textContent = chosen?.emoji || '🪴';
    document.querySelector('#gift-sent-message').textContent = message;
    document.querySelector('#gift-form-view').hidden = true;
    document.querySelector('#gift-success').hidden = false;
  }, 450);
});
document.querySelector('.gift-done').addEventListener('click', closeGrowthModal);

loadPlant();
