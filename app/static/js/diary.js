let csrf = '';
let plants = [];
let selectedPlant = null;
let entries = [];
let recentEntries = [];
let currentEntry = null;
let serverToday = '';
let selectedDate = '';
let editorEntry = null;

const now = new Date();
let viewDate = new Date(now.getFullYear(), now.getMonth(), 1);
const calendar = document.querySelector('#calendar');
const monthTitle = document.querySelector('#month-title');
const plantSelect = document.querySelector('#diary-plant-select');
const newEntryButton = document.querySelector('#new-entry');
const emptyCreateButton = document.querySelector('#empty-create');
const loadingPanel = document.querySelector('#diary-loading');
const emptyPanel = document.querySelector('#diary-empty');
const diaryView = document.querySelector('#diary-view');
const alertBox = document.querySelector('#diary-alert');
const editor = document.querySelector('#diary-editor');
const diaryForm = document.querySelector('#diary-form');
const titleInput = document.querySelector('#diary-title-input');
const contentInput = document.querySelector('#diary-content-input');
const editorError = document.querySelector('#diary-editor-error');

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
}

function dateKey(year, month, day) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function formatDate(value) {
  if (!value) return '';
  const [year, month, day] = value.split('-').map(Number);
  return `${year}년 ${month}월 ${day}일`;
}

function formatShortDate(value) {
  if (!value) return '';
  const [, month, day] = value.split('-').map(Number);
  return `${month}월 ${day}일`;
}

function showAlert(message = '') {
  alertBox.textContent = message;
  alertBox.hidden = !message;
}

function showToast(message) {
  const toast = document.querySelector('.toast');
  toast.textContent = message;
  toast.classList.add('show');
  window.setTimeout(() => toast.classList.remove('show'), 2300);
}

async function loadCsrf() {
  const response = await fetch('/api/v1/auth/csrf', { credentials: 'same-origin' });
  const payload = await response.json();
  if (!response.ok) throw new Error('보안 정보를 불러오지 못했습니다.');
  csrf = payload.data.csrfToken;
}

async function apiRequest(path, options = {}) {
  const method = String(options.method || 'GET').toUpperCase();
  const mutating = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);
  if (mutating && !csrf) await loadCsrf();
  const response = await fetch(path, {
    ...options,
    method,
    credentials: 'same-origin',
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(mutating ? { 'X-CSRF-Token': csrf } : {}),
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (response.status === 401) {
    location.href = `/login.html?next=${encodeURIComponent(location.pathname + location.search)}`;
    throw new Error('로그인이 필요합니다.');
  }
  if (!response.ok) throw new Error(payload.error?.message || '요청을 처리하지 못했습니다.');
  return payload;
}

function setPanel(panel) {
  loadingPanel.hidden = panel !== 'loading';
  emptyPanel.hidden = panel !== 'empty';
  diaryView.hidden = panel !== 'entry';
}

function updateCreateControls() {
  const isOwner = selectedPlant?.accessType === 'OWNER';
  const isToday = selectedDate === serverToday;
  newEntryButton.hidden = !isOwner || !isToday;
  emptyCreateButton.hidden = !isOwner || !isToday;
  newEntryButton.textContent = currentEntry
    ? '✏️ 오늘 일기 수정하기'
    : '✨ AI 성장일기 만들기';
  document.querySelector('#diary-empty-copy').textContent = isToday
    ? (isOwner
      ? '오늘의 돌봄과 대화를 모아 식물이 직접 일기를 쓸 수 있어요.'
      : '오늘의 성장일기는 현재 식물 주인이 작성할 수 있어요.')
    : '이 날짜에는 저장된 성장일기가 없습니다.';
}

function renderCalendar() {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth() + 1;
  const firstDay = new Date(year, month - 1, 1).getDay();
  const lastDate = new Date(year, month, 0).getDate();
  const previousLast = new Date(year, month - 1, 0).getDate();
  const byDate = new Map(entries.map(entry => [entry.diaryDate, entry]));
  monthTitle.textContent = `${year}년 ${month}월`;
  calendar.innerHTML = '';

  for (let offset = firstDay - 1; offset >= 0; offset -= 1) {
    calendar.insertAdjacentHTML('beforeend', `<button class="day muted" type="button" disabled>${previousLast - offset}</button>`);
  }
  for (let day = 1; day <= lastDate; day += 1) {
    const key = dateKey(year, month, day);
    const entry = byDate.get(key);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'day';
    button.textContent = day;
    button.dataset.date = key;
    if (entry) {
      button.classList.add('has-entry', entry.growthTendency.toLowerCase());
      button.setAttribute('aria-label', `${formatDate(key)} 성장일기 있음`);
    }
    if (key === serverToday) button.classList.add('today');
    if (key === selectedDate) button.classList.add('selected');
    button.addEventListener('click', () => selectDate(key));
    calendar.appendChild(button);
  }
}

function renderMonthSummary(summary) {
  document.querySelector('#month-record-count').textContent = `이번 달 기록 ${summary.entryCount}개`;
  document.querySelector('#month-record-summary').textContent = summary.entryCount
    ? `긍정 ${summary.positiveCount}일 · 부정 ${summary.negativeCount}일 · 순 에너지 ${summary.netEnergy >= 0 ? '+' : ''}${summary.netEnergy}`
    : '오늘의 마음을 기록해 보세요.';
}

function renderActivity(summary = {}) {
  const list = document.querySelector('#activity-list');
  const actions = summary.careActions || [];
  const chat = summary.chat || {};
  const icons = { WATER: '💧', SUNLIGHT: '🌞', PET: '✋', IGNORE: '🌫️' };
  const cards = actions.map(action => {
    const delta = Number(action.positiveDelta || 0) - Number(action.negativeDelta || 0);
    return `<article class="activity-card ${action.actionType === 'IGNORE' ? 'negative' : ''}"><span class="activity-icon">${icons[action.actionType] || '🌱'}</span><div><h3>${escapeHtml(action.label)} ${action.count > 1 ? `${action.count}회` : ''}</h3><p>성장 +${action.growthDelta} · 긍정 +${action.positiveDelta} · 부정 +${action.negativeDelta}</p></div><strong>${delta >= 0 ? '+' : ''}${delta}</strong></article>`;
  });
  if (chat.messageCount) {
    const delta = Number(chat.positiveDelta || 0) - Number(chat.negativeDelta || 0);
    cards.push(`<article class="activity-card chat"><span class="activity-icon">💬</span><div><h3>식물과 대화 ${chat.messageCount}개</h3><p>${escapeHtml(chat.representativeMessage || '따뜻한 이야기를 나눴어요.')}</p></div><strong>${delta >= 0 ? '+' : ''}${delta}</strong></article>`);
  }
  list.innerHTML = cards.join('') || '<p class="activity-empty">저장된 활동이 없습니다.</p>';

  const totals = summary.totals || {};
  const net = Number(totals.positiveDelta || 0) - Number(totals.negativeDelta || 0);
  document.querySelector('#daily-energy-value').textContent = `${net >= 0 ? '+' : ''}${net}`;
  document.querySelector('#daily-energy-bar').style.width = `${Math.min(100, Math.abs(net) * 10)}%`;
  document.querySelector('#daily-energy-copy').textContent = net > 0
    ? '행복한 마음이 차곡차곡 쌓였어요!'
    : (net < 0 ? '조금 외롭고 속상한 하루였어요.' : '차분한 하루였어요.');
}

function renderEntry(entry) {
  currentEntry = entry;
  setPanel('entry');
  document.querySelector('#selected-date-label').textContent = `${formatShortDate(entry.diaryDate)}의 기록`;
  document.querySelector('#entry-title').textContent = entry.title;
  document.querySelector('#entry-date').textContent = formatDate(entry.diaryDate);
  document.querySelector('#paper-entry-title').textContent = entry.title;
  document.querySelector('#paper-growth-copy').textContent = `성장도 ${entry.growthScore} · ${entry.mood || '평온한 마음'}`;
  document.querySelector('#paper-sign').textContent = `- ${selectedPlant.name}가 쓴 성장일기 · ${entry.author?.nickname || '주인'} -`;
  document.querySelector('#edit-entry').hidden = !entry.canEdit;
  const paragraphs = entry.content.split(/\n+/).filter(Boolean);
  document.querySelector('#entry-content').innerHTML = (paragraphs.length ? paragraphs : [entry.content])
    .map(line => `<p>${escapeHtml(line)}</p>`).join('');
  renderActivity(entry.activitySummary);
  updateCreateControls();
  renderCalendar();
}

function renderEmpty(day) {
  currentEntry = null;
  selectedDate = day;
  setPanel('empty');
  document.querySelector('#selected-date-label').textContent = day === serverToday ? '오늘의 기록' : `${formatShortDate(day)}의 기록`;
  document.querySelector('#entry-title').textContent = '아직 기록되지 않은 하루예요';
  renderActivity({});
  updateCreateControls();
  renderCalendar();
}

async function selectDate(day) {
  selectedDate = day;
  const summary = entries.find(entry => entry.diaryDate === day);
  if (!summary) {
    renderEmpty(day);
    return;
  }
  setPanel('loading');
  try {
    const payload = await apiRequest(`/api/v1/diary/${summary.id}`);
    renderEntry(payload.data.entry);
  } catch (error) {
    showAlert(error.message);
    renderEmpty(day);
  }
}

function renderRecent() {
  const container = document.querySelector('#entry-cards');
  if (!recentEntries.length) {
    container.innerHTML = '<p class="empty-archive">아직 저장된 성장기록이 없습니다.</p>';
    return;
  }
  container.innerHTML = recentEntries.map(entry => {
    const icon = entry.growthTendency === 'NEGATIVE' ? '🌧️' : '🌱';
    const totals = entry.activitySummary?.totals || {};
    const net = Number(totals.positiveDelta || 0) - Number(totals.negativeDelta || 0);
    return `<article data-entry-id="${entry.id}" data-entry-date="${entry.diaryDate}"><div><span>${icon}</span><small>${formatShortDate(entry.diaryDate)}</small></div><h3>${escapeHtml(entry.title)}</h3><p>${escapeHtml(entry.preview)}</p><b class="${entry.growthTendency === 'NEGATIVE' ? 'sad' : ''}">${escapeHtml(entry.mood || '평온')} · ${net >= 0 ? '+' : ''}${net}</b></article>`;
  }).join('');
  container.querySelectorAll('article').forEach(card => card.addEventListener('click', async () => {
    const date = card.dataset.entryDate;
    const [year, month] = date.split('-').map(Number);
    if (viewDate.getFullYear() !== year || viewDate.getMonth() + 1 !== month) {
      viewDate = new Date(year, month - 1, 1);
      await loadMonth(date);
    } else {
      await selectDate(date);
    }
    document.querySelector('.today-layout').scrollIntoView({ behavior: 'smooth' });
  }));
}

async function loadMonth(preferredDate = null) {
  if (!selectedPlant) return;
  showAlert('');
  setPanel('loading');
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth() + 1;
  try {
    const payload = await apiRequest(`/api/v1/plants/${selectedPlant.id}/diary?year=${year}&month=${month}`);
    selectedPlant = { ...selectedPlant, ...payload.data.plant };
    entries = payload.data.entries;
    recentEntries = payload.data.recentEntries;
    serverToday = payload.data.today;
    renderMonthSummary(payload.data.summary);
    renderRecent();
    renderCalendar();

    const todayInMonth = serverToday.startsWith(`${year}-${String(month).padStart(2, '0')}`);
    const target = preferredDate
      || (todayInMonth ? serverToday : entries.at(-1)?.diaryDate)
      || dateKey(year, month, 1);
    await selectDate(target);
  } catch (error) {
    showAlert(error.message);
    setPanel('empty');
  }
}

function updatePlantHeader() {
  document.querySelector('#diary-plant-name').textContent = selectedPlant.name;
  document.querySelector('#diary-plant-icon').textContent = selectedPlant.emoji || '🪴';
  document.querySelector('#paper-plant-icon').textContent = selectedPlant.emoji || '🪴';
  document.querySelector('#diary-plant-meta').textContent = selectedPlant.accessType === 'OWNER'
    ? `성장도 ${selectedPlant.growthScore} · 현재 키우는 식물`
    : '내가 작성한 성장일기 보관함';
  const back = document.querySelector('#diary-back');
  if (selectedPlant.accessType === 'OWNER') {
    back.href = `/dashboard-v2.html?plantId=${selectedPlant.id}`;
    back.textContent = '← 식물 키우기로 돌아가기';
  } else {
    back.href = '/my-plants.html';
    back.textContent = '← 내 식물로 돌아가기';
  }
}

async function choosePlant(plantId) {
  selectedPlant = plants.find(plant => plant.id === Number(plantId)) || plants[0];
  if (!selectedPlant) return;
  plantSelect.value = String(selectedPlant.id);
  history.replaceState({}, '', `/diary.html?plantId=${selectedPlant.id}`);
  updatePlantHeader();
  const [year, month] = (serverToday || dateKey(now.getFullYear(), now.getMonth() + 1, now.getDate())).split('-').map(Number);
  viewDate = new Date(year, month - 1, 1);
  await loadMonth();
}

async function loadPlants() {
  try {
    const payload = await apiRequest('/api/v1/diary/plants');
    plants = payload.data.plants;
    if (!plants.length) {
      location.href = '/plant-select.html';
      return;
    }
    plantSelect.innerHTML = plants.map(plant => (
      `<option value="${plant.id}">${escapeHtml(plant.name)}${plant.accessType === 'AUTHOR_ARCHIVE' ? ' · 보관 기록' : ''}</option>`
    )).join('');
    const requestedId = Number(new URLSearchParams(location.search).get('plantId'));
    await choosePlant(requestedId);
  } catch (error) {
    showAlert(error.message);
    setPanel('empty');
  }
}

function updateEditorCounts() {
  document.querySelector('#diary-title-count').textContent = titleInput.value.length;
  document.querySelector('#diary-content-count').textContent = contentInput.value.length;
}

function openEditor(entry = null, draft = null) {
  editorEntry = entry;
  titleInput.value = entry?.title || draft?.title || '';
  contentInput.value = entry?.content || draft?.content || '';
  document.querySelector('#diary-editor-title').textContent = entry ? '성장일기 수정' : 'AI 성장일기 초안';
  document.querySelector('#editor-description').textContent = entry
    ? '제목과 내용을 수정할 수 있어요. 저장 당시의 성장 상태는 유지됩니다.'
    : (draft?.fallback
      ? 'AI 연결이 원활하지 않아 기본 초안을 만들었어요. 자유롭게 다듬어 주세요.'
      : '식물이 오늘을 돌아보며 쓴 초안이에요. 자유롭게 다듬어 주세요.');
  editorError.textContent = '';
  updateEditorCounts();
  editor.hidden = false;
  document.body.style.overflow = 'hidden';
  titleInput.focus();
}

function closeEditor() {
  editor.hidden = true;
  document.body.style.overflow = '';
  editorEntry = null;
}

async function createOrEditToday() {
  if (currentEntry && currentEntry.diaryDate === serverToday) {
    openEditor(currentEntry);
    return;
  }
  newEntryButton.disabled = true;
  emptyCreateButton.disabled = true;
  const originalText = newEntryButton.textContent;
  newEntryButton.textContent = '식물이 일기를 쓰는 중…';
  try {
    const payload = await apiRequest(`/api/v1/plants/${selectedPlant.id}/diary/draft`, { method: 'POST' });
    openEditor(null, payload.data.draft);
  } catch (error) {
    showAlert(error.message);
  } finally {
    newEntryButton.disabled = false;
    emptyCreateButton.disabled = false;
    newEntryButton.textContent = originalText;
  }
}

diaryForm.addEventListener('submit', async event => {
  event.preventDefault();
  const title = titleInput.value.trim();
  const content = contentInput.value.trim();
  if (!title || !content) {
    editorError.textContent = '제목과 내용을 모두 입력해 주세요.';
    return;
  }
  const saveButton = diaryForm.querySelector('.editor-save');
  saveButton.disabled = true;
  saveButton.textContent = '저장하는 중…';
  try {
    const path = editorEntry
      ? `/api/v1/diary/${editorEntry.id}`
      : `/api/v1/plants/${selectedPlant.id}/diary/today`;
    const method = editorEntry ? 'PATCH' : 'PUT';
    const payload = await apiRequest(path, {
      method,
      body: JSON.stringify({ title, content })
    });
    const savedDate = payload.data.entry.diaryDate;
    closeEditor();
    await loadMonth(savedDate);
    showToast('성장일기를 저장했어요. 🌱');
  } catch (error) {
    editorError.textContent = error.message;
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = '저장하기';
  }
});

plantSelect.addEventListener('change', () => choosePlant(plantSelect.value));
document.querySelector('#prev-month').addEventListener('click', () => {
  viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1);
  loadMonth();
});
document.querySelector('#next-month').addEventListener('click', () => {
  viewDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1);
  loadMonth();
});
newEntryButton.addEventListener('click', createOrEditToday);
emptyCreateButton.addEventListener('click', createOrEditToday);
document.querySelector('#edit-entry').addEventListener('click', () => currentEntry && openEditor(currentEntry));
document.querySelector('.editor-cancel').addEventListener('click', closeEditor);
document.querySelector('.diary-editor-backdrop').addEventListener('click', closeEditor);
document.querySelector('#show-month').addEventListener('click', () => {
  document.querySelector('.calendar-panel').scrollIntoView({ behavior: 'smooth' });
  showToast(`${viewDate.getMonth() + 1}월 기록 ${entries.length}개를 달력에 표시했어요.`);
});
titleInput.addEventListener('input', updateEditorCounts);
contentInput.addEventListener('input', updateEditorCounts);
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !editor.hidden) closeEditor();
});

loadPlants();
