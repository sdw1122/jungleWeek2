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
      reactions: { sprout: 0, water: 0, sun: 0, heart: 0 },
      replies: []
    },
    {
      id: 'seed-2',
      author: '다육이엄마',
      content: 'Farmda에서 만난 인연 덕분에 식물 키우는 재미가 두 배가 됐어요. 감사합니다!',
      createdAt: Date.now() - 1000 * 60 * 60 * 5,
      reactions: { sprout: 0, water: 0, sun: 0, heart: 0 },
      replies: []
    },
    {
      id: 'seed-1',
      author: '초록정원사',
      content: '처음 시작할 땐 막막했는데 다들 응원해주셔서 여기까지 왔네요. 고맙습니다 :)',
      createdAt: Date.now() - 1000 * 60 * 60 * 27,
      reactions: { sprout: 0, water: 0, sun: 0, heart: 0 },
      replies: []
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
      (entry) => {
        // Fallback for older entries without reactions/replies
        const rx = entry.reactions || { sprout: 0, water: 0, sun: 0, heart: 0 };
        const rp = entry.replies || [];
        
        const repliesHtml = rp.map(r => `
          <div style="background:#f8f9fa; padding:10px; margin-top:10px; border-radius:8px; border-left:3px solid #12a84e;">
            <b style="color:#12a84e; margin-right:8px;">👑 ${escapeHtml(r.author)}</b>
            <span>${escapeHtml(r.content)}</span>
          </div>
        `).join('');

        return `<article class="entry-card" data-id="${escapeHtml(entry.id)}">
        <div class="entry-card-meta">
          <span class="entry-author">${escapeHtml(entry.author)}</span>
          <span>${timeAgo(entry.createdAt)}</span>
          ${entry.author === CURRENT_USER ? `
            <button class="entry-edit" type="button" aria-label="수정" style="border:none;background:none;color:#888;cursor:pointer;font-size:12px;margin-left:auto;">수정</button>
            <button class="entry-delete" type="button" aria-label="삭제" style="border:none;background:none;color:#c01461;cursor:pointer;font-size:12px;margin-left:5px;">삭제</button>
          ` : ''}
        </div>
        <p class="entry-content">${escapeHtml(entry.content)}</p>
        <div style="display:flex; gap:8px; margin-top:15px; flex-wrap:wrap;">
            <button class="reaction-btn" data-type="sprout" style="background:#f1f5f9;border:none;border-radius:20px;padding:5px 10px;cursor:pointer;">🌱 ${rx.sprout}</button>
            <button class="reaction-btn" data-type="water" style="background:#f1f5f9;border:none;border-radius:20px;padding:5px 10px;cursor:pointer;">💧 ${rx.water}</button>
            <button class="reaction-btn" data-type="sun" style="background:#f1f5f9;border:none;border-radius:20px;padding:5px 10px;cursor:pointer;">☀️ ${rx.sun}</button>
            <button class="reaction-btn" data-type="heart" style="background:#f1f5f9;border:none;border-radius:20px;padding:5px 10px;cursor:pointer;">❤️ ${rx.heart}</button>
            <button class="reply-toggle" style="background:none;border:none;color:#075cc9;font-weight:600;margin-left:auto;cursor:pointer;">💬 답글 달기</button>
        </div>
        <div class="reply-container" style="display:none; margin-top:10px; display:flex; gap:10px;">
            <input type="text" class="reply-input" placeholder="답글을 입력하세요..." style="flex-grow:1; padding:8px; border:1px solid #ddd; border-radius:6px;">
            <button class="reply-submit" style="background:#293241; color:#fff; border:none; padding:0 15px; border-radius:6px; cursor:pointer;">등록</button>
        </div>
        ${repliesHtml}
      </article>`;
      }
    )
    .join('');
}

entryList.addEventListener('click', (event) => {
  const card = event.target.closest('.entry-card');
  if (!card) return;
  const id = card.dataset.id;
  
  // Delete
  if (event.target.closest('.entry-delete')) {
    if (!confirm('이 방명록을 삭제할까요?')) return;
    const entries = loadEntries().filter((entry) => entry.id !== id);
    saveEntries(entries);
    render();
  }
  
  // Edit
  if (event.target.closest('.entry-edit')) {
    const contentP = card.querySelector('.entry-content');
    const oldContent = contentP.innerText;
    const newContent = prompt('수정할 내용을 입력하세요:', oldContent);
    if (newContent !== null && newContent.trim() !== '') {
      const entries = loadEntries();
      const entry = entries.find(e => e.id === id);
      if (entry) {
        entry.content = newContent.trim();
        saveEntries(entries);
        render();
      }
    }
  }

  // Reaction
  if (event.target.closest('.reaction-btn')) {
    const type = event.target.closest('.reaction-btn').dataset.type;
    const entries = loadEntries();
    const entry = entries.find(e => e.id === id);
    if (entry) {
      if (!entry.reactions) entry.reactions = { sprout: 0, water: 0, sun: 0, heart: 0 };
      entry.reactions[type]++;
      saveEntries(entries);
      render();
    }
  }

  // Reply Toggle
  if (event.target.closest('.reply-toggle')) {
    const replyContainer = card.querySelector('.reply-container');
    replyContainer.style.display = replyContainer.style.display === 'none' ? 'flex' : 'none';
  }

  // Reply Submit
  if (event.target.closest('.reply-submit')) {
    const input = card.querySelector('.reply-input');
    const content = input.value.trim();
    if (!content) return;
    const entries = loadEntries();
    const entry = entries.find(e => e.id === id);
    if (entry) {
      if (!entry.replies) entry.replies = [];
      entry.replies.push({ author: '주인장', content });
      saveEntries(entries);
      render();
    }
  }
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
    reactions: { sprout: 0, water: 0, sun: 0, heart: 0 },
    replies: []
  });
  saveEntries(entries);
  closeModal();
  render();
});

render();
