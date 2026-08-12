let chosen = null;
let completionShown = false;
let csrf = '';
let lastAiEmotion = null;

const messages = document.querySelector('#messages');
const messageList = document.querySelector('#message-list');
const loadOlderMessages = document.querySelector('#load-older-messages');
const stagePlant = document.querySelector('#seed');
const seedActions = document.querySelector('#seed-actions');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const actionButtons = document.querySelectorAll('[data-action]');
const openGiftButton = document.querySelector('#open-gift');
let nextBeforeMessageId = null;
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
  water: '시원해요! 뿌리가 촉촉해졌어요. 💧',
  sun: '따뜻한 햇빛 덕분에 힘이 나요! ☀️',
  pet: '정성스러운 손길이 느껴져요. 🌱',
  ignore: '조금 외로워요. 저를 잊지 말아주세요. 🌧️'
};
const apiActions = { water: 'WATER', sun: 'SUNLIGHT', pet: 'PET', ignore: 'IGNORE' };

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
}

function messageMarkup(role, content, speakerNickname = null) {
  const isUser = role === 'USER';
  const speaker = isUser && speakerNickname
    ? `<small class="message-speaker">${escapeHtml(speakerNickname)}</small>`
    : '';
  return `<div class="message-row ${isUser ? 'user' : 'plant'}">${speaker}<p${isUser ? ' class="user"' : ''}>${escapeHtml(content)}</p></div>`;
}

function appendMessage(role, content, speakerNickname = null) {
  messageList.insertAdjacentHTML('beforeend', messageMarkup(role, content, speakerNickname));
}

async function loadChatHistory(beforeId = null) {
  const query = new URLSearchParams({ limit: '50' });
  if (beforeId) query.set('beforeId', String(beforeId));
  const previousHeight = messages.scrollHeight;
  const payload = await apiRequest(`/api/chat/${chosen.id}/messages?${query}`);
  const historyMessages = payload.data.messages;
  const markup = historyMessages.map(item => (
    messageMarkup(item.role, item.content, item.speakerNickname)
  )).join('');

  if (beforeId) {
    messageList.insertAdjacentHTML('afterbegin', markup);
    messages.scrollTop += messages.scrollHeight - previousHeight;
  } else if (historyMessages.length) {
    messageList.innerHTML = markup;
    messages.scrollTop = messages.scrollHeight;
  } else {
    messageList.innerHTML = '<p>씨앗이 심어졌습니다. 먼저 정성껏 돌봐주세요!</p>';
  }
  nextBeforeMessageId = payload.data.nextBeforeId;
  loadOlderMessages.hidden = !nextBeforeMessageId;
}

loadOlderMessages.addEventListener('click', async () => {
  if (!nextBeforeMessageId || loadOlderMessages.disabled) return;
  loadOlderMessages.disabled = true;
  try {
    await loadChatHistory(nextBeforeMessageId);
  } catch (error) {
    appendMessage('PLANT', error.message);
  } finally {
    loadOlderMessages.disabled = false;
  }
});

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
  const plantName = chosen.displayName || chosen.name;
  const speciesName = chosen.speciesName || chosen.name;
  const isNegative = chosen.negativeEnergy > chosen.positiveEnergy;
  const seedStyle = seedStyles[speciesName] || 'monstera';
  const stageStyle = stageStyles[stage.name];
  const visualKey = `${seedStyle}-${stageStyle}-${isNegative ? 'wilted' : 'healthy'}`;

  document.querySelector('#plant-name').textContent = plantName;
  document.querySelector('#diary-link').href = `/diary.html?plantId=${chosen.id}`;
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
  const storedEmotion = ['POSITIVE', 'NEGATIVE'].includes(chosen.mood)
    ? null
    : chosen.mood;
  const currentEmotion = lastAiEmotion || storedEmotion;
  document.querySelector('#mood-copy').textContent = currentEmotion
    ? `현재 기분: ${currentEmotion}`
    : (isNegative ? '관심이 조금 부족해요. 따뜻하게 돌봐주세요.' : stage.mood);

  seedActions.hidden = false;
  chatForm.hidden = total < 5;
  openGiftButton.hidden = total < 100;
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

function showCompletion(previousScore) {
  if (previousScore < 100 && chosen?.growthScore >= 100 && !completionShown) {
    completionShown = true;
    window.setTimeout(() => {
      openGiftModal();
    }, 500);
  }
}

async function care(actionType, note = null, sentiment = 'POSITIVE') {
  const previousScore = chosen.growthScore;
  const payload = await apiRequest(`/api/v1/plants/${chosen.id}/care`, {
    method: 'POST',
    body: JSON.stringify({ actionType, note, sentiment })
  });
  chosen = payload.data.plant;
  lastAiEmotion = null;
  renderGrowth(true);
  showCompletion(previousScore);
}

actionButtons.forEach(button => button.addEventListener('click', async () => {
  if (!chosen || button.disabled) return;
  actionButtons.forEach(item => { item.disabled = true; });
  const action = button.dataset.action;
  try {
    await care(apiActions[action]);
    appendMessage('USER', replies[action]);
    messages.scrollTop = messages.scrollHeight;
    stagePlant.animate(
      [{ transform: 'scale(.94)' }, { transform: 'scale(1.08)' }, { transform: 'scale(1)' }],
      { duration: 320 }
    );
  } catch (error) {
    appendMessage('PLANT', error.message);
  } finally {
    actionButtons.forEach(item => { item.disabled = false; });
  }
}));

chatForm.addEventListener('submit', async event => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text || !chosen || chatInput.disabled) return;

  appendMessage('USER', text);
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
    appendMessage('PLANT', payload.response);
    renderGrowth(true);
  } catch (error) {
    appendMessage('PLANT', error.message);
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
      const firstPlant = payload.data.plants[0];
      const detailPayload = await apiRequest(`/api/v1/plants/${firstPlant.id}`);
      chosen = detailPayload.data.plant;
      history.replaceState({}, '', `dashboard-v2.html?plantId=${firstPlant.id}`);
    }
    renderGrowth(false);
    await loadChatHistory();
    if (chosen.receivedGift) showReceivedGift(chosen.receivedGift);
  } catch (error) {
    messageList.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
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
    appendMessage('PLANT', error.message);
  }
});

const growthModal = document.querySelector('#growth-modal');
function openGiftModal() {
  document.querySelector('#gift-form-view').hidden = false;
  document.querySelector('#gift-success').hidden = true;
  giftError.textContent = '';
  growthModal.hidden = false;
  document.body.style.overflow = 'hidden';
}
function closeGrowthModal() {
  growthModal.hidden = true;
  document.body.style.overflow = '';
}
openGiftButton.addEventListener('click', openGiftModal);
document.querySelector('.modal-later').addEventListener('click', closeGrowthModal);
growthModal.querySelector('.growth-modal-backdrop').addEventListener('click', closeGrowthModal);
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
giftForm.addEventListener('submit', async event => {
  event.preventDefault();
  const nickname = giftNickname.value.trim();
  const message = giftMessage.value.trim();
  if (nickname.length < 2) {
    giftError.textContent = '닉네임을 2자 이상 입력해주세요.';
    giftNickname.focus();
    return;
  }
  if (!window.confirm(`${nickname}님에게 이 식물을 선물할까요? 선물하면 소유권이 즉시 이전됩니다.`)) {
    return;
  }
  const submitButton = giftForm.querySelector('.gift-submit');
  submitButton.disabled = true;
  submitButton.querySelector('b').textContent = '선물 카드를 만드는 중…';
  try {
    const payload = await apiRequest(`/api/v1/plants/${chosen.id}/gift`, {
      method: 'POST',
      body: JSON.stringify({ recipientNickname: nickname, message })
    });
    document.querySelector('#gift-recipient').textContent = payload.data.gift.recipient.nickname;
    document.querySelector('#gift-plant-name').textContent = chosen?.displayName || chosen?.name || '식물';
    document.querySelector('#gift-plant-icon').textContent = chosen?.emoji || '🪴';
    document.querySelector('#gift-sent-message').textContent = message;
    document.querySelector('#gift-form-view').hidden = true;
    document.querySelector('#gift-success').hidden = false;
  } catch (error) {
    giftError.textContent = error.message;
    submitButton.disabled = false;
    submitButton.querySelector('b').textContent = '이 식물 선물하기';
  }
});
document.querySelector('#gift-success .gift-done').addEventListener('click', () => {
  location.href = '/my-plants.html';
});

const receivedGiftModal = document.querySelector('#received-gift-modal');
const receivedGiftConfirm = document.querySelector('#received-gift-confirm');
let receivedGift = null;

function showReceivedGift(gift) {
  receivedGift = gift;
  document.querySelector('#received-gift-sender').textContent = gift.sender?.nickname || '친구';
  document.querySelector('#received-gift-plant').textContent = chosen?.displayName || chosen?.name || '식물';
  document.querySelector('#received-gift-icon').textContent = chosen?.emoji || '🪴';
  document.querySelector('#received-gift-message').textContent = gift.message || '';
  document.querySelector('#received-gift-error').textContent = '';
  receivedGiftModal.hidden = false;
  document.body.style.overflow = 'hidden';
}

receivedGiftConfirm.addEventListener('click', async () => {
  if (!receivedGift || receivedGiftConfirm.disabled) return;
  receivedGiftConfirm.disabled = true;
  receivedGiftConfirm.textContent = '확인하는 중…';
  try {
    await apiRequest(`/api/v1/gifts/${receivedGift.id}/acknowledge`, { method: 'POST' });
    chosen.receivedGift = null;
    receivedGift = null;
    receivedGiftModal.hidden = true;
    document.body.style.overflow = '';
  } catch (error) {
    document.querySelector('#received-gift-error').textContent = error.message;
  } finally {
    receivedGiftConfirm.disabled = false;
    receivedGiftConfirm.textContent = '선물 확인하기';
  }
});

loadPlant();
