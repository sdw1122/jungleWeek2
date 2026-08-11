const STORAGE_KEY = 'farmda_guestbook_entries';
const CURRENT_USER = '나';

function loadEntries() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) {
    try {
      return JSON.parse(raw);
    } catch (err) {
      /* fall through to reseed */
    }
  }
  const seed = [
    {
      id: 'seed-3',
      author: '몬스테라집사',
      content: '식물 덕분에 아침마다 웃게 돼요. 다들 오늘도 좋은 하루 보내세요 🌱',
      createdAt: Date.now() - 1000 * 60 * 40,
    },
    {
      id: 'seed-2',
      author: '다육이엄마',
      content: 'Farmda에서 만난 인연 덕분에 식물 키우는 재미가 두 배가 됐어요. 감사합니다!',
      createdAt: Date.now() - 1000 * 60 * 60 * 5,
    },
    {
      id: 'seed-1',
      author: '초록정원사',
      content: '처음 시작할 땐 막막했는데 다들 응원해주셔서 여기까지 왔네요. 고맙습니다 :)',
      createdAt: Date.now() - 1000 * 60 * 60 * 27,
    },
  ];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(seed));
  return seed;
}

function saveEntries(entries) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

function timeAgo(timestamp) {
  const diff = Math.max(0, Date.now() - timestamp);
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) return '방금 전';
  if (diff < hour) return `${Math.floor(diff / minute)}분 전`;
  if (diff < day) return `${Math.floor(diff / hour)}시간 전`;
  if (diff < day * 7) return `${Math.floor(diff / day)}일 전`;
  return new Date(timestamp).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

const entryList = document.querySelector('#entry-list');
const entryCount = document.querySelector('#entry-count');
const emptyState = document.querySelector('#guestbook-empty');
const overlay = document.querySelector('#write-overlay');
const form = document.querySelector('#write-form');

function render() {
  const entries = loadEntries().slice().sort((a, b) => b.createdAt - a.createdAt);
  entryCount.textContent = `방명록 ${entries.length}개`;
  emptyState.hidden = entries.length > 0;

  entryList.innerHTML = entries
    .map(
      (entry) => `<article class="entry-card" data-id="${escapeHtml(entry.id)}">
        <div class="entry-card-meta">
          <span class="entry-author">${escapeHtml(entry.author)}</span>
          <span>${timeAgo(entry.createdAt)}</span>
          ${entry.author === CURRENT_USER ? '<button class="entry-delete" type="button" aria-label="삭제">×</button>' : ''}
        </div>
        <p class="entry-content">${escapeHtml(entry.content)}</p>
      </article>`
    )
    .join('');
}

entryList.addEventListener('click', (event) => {
  const button = event.target.closest('.entry-delete');
  if (!button) return;
  const id = button.closest('.entry-card').dataset.id;
  if (!confirm('이 방명록을 삭제할까요?')) return;
  const entries = loadEntries().filter((entry) => entry.id !== id);
  saveEntries(entries);
  render();
});

function openModal() {
  overlay.hidden = false;
  document.querySelector('#write-content').focus();
}

function closeModal() {
  overlay.hidden = true;
  form.reset();
}

document.querySelector('#open-write').addEventListener('click', openModal);
document.querySelector('#write-close').addEventListener('click', closeModal);
document.querySelector('#write-cancel').addEventListener('click', closeModal);
overlay.addEventListener('click', (event) => {
  if (event.target === overlay) closeModal();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !overlay.hidden) closeModal();
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const content = document.querySelector('#write-content').value.trim();
  if (!content) return;
  const entries = loadEntries();
  entries.push({
    id: `${Date.now()}`,
    author: CURRENT_USER,
    content,
    createdAt: Date.now(),
  });
  saveEntries(entries);
  closeModal();
  render();
});

render();
