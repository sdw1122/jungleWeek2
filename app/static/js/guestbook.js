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
      reactions: { like: 0, dislike: 0 },
      replies: []
    },
    {
      id: 'seed-2',
      author: '다육이엄마',
      content: 'Farmda에서 만난 인연 덕분에 식물 키우는 재미가 두 배가 됐어요. 감사합니다!',
      createdAt: Date.now() - 1000 * 60 * 60 * 5,
      reactions: { like: 0, dislike: 0 },
      replies: []
    },
    {
      id: 'seed-1',
      author: '초록정원사',
      content: '처음 시작할 땐 막막했는데 다들 응원해주셔서 여기까지 왔네요. 고맙습니다 :)',
      createdAt: Date.now() - 1000 * 60 * 60 * 27,
      reactions: { like: 0, dislike: 0 },
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
        const rx = entry.reactions || { like: 0, dislike: 0 };
        const rp = entry.replies || [];
        
        const repliesHtml = rp.map(r => `
          <div style="background:#f8f9fa; padding:12px; margin-top:10px; border-radius:8px; border-left:3px solid #dfe3e8; font-size:14px; color:#333;">
            <b style="color:#555; margin-right:8px;">${escapeHtml(r.author)}</b>
            <span>${escapeHtml(r.content)}</span>
          </div>
        `).join('');

        return `<article class="entry-card" data-id="${escapeHtml(entry.id)}" style="padding:20px; border-radius:12px; border:1px solid #eee; margin-bottom:15px; box-shadow:0 2px 8px rgba(0,0,0,0.02);">
        <div class="entry-card-meta" style="display:flex; align-items:center; margin-bottom:10px;">
          <strong class="entry-author" style="font-size:15px; color:#222; margin-right:10px;">${escapeHtml(entry.author)}</strong>
          <span style="font-size:13px; color:#999;">${timeAgo(entry.createdAt)}</span>
          ${entry.author === CURRENT_USER ? `
            <div style="margin-left:auto; display:flex; gap:10px;">
              <button class="entry-edit" type="button" aria-label="수정" style="border:none;background:none;color:#888;cursor:pointer;font-size:13px;">수정</button>
              <button class="entry-delete" type="button" aria-label="삭제" style="border:none;background:none;color:#ff6b6b;cursor:pointer;font-size:13px;">삭제</button>
            </div>
          ` : ''}
        </div>
        <p class="entry-content" style="font-size:15px; line-height:1.6; color:#444; margin:10px 0;">${escapeHtml(entry.content)}</p>
        
        <div style="display:flex; gap:8px; margin-top:15px; align-items:center;">
            <button class="reaction-btn" data-type="like" style="background:#f4f6f8; color:#555; border:1px solid #eee; border-radius:20px; padding:6px 12px; font-size:13px; cursor:pointer; transition:all 0.2s;">👍 ${rx.like || 0}</button>
            <button class="reaction-btn" data-type="dislike" style="background:#f4f6f8; color:#555; border:1px solid #eee; border-radius:20px; padding:6px 12px; font-size:13px; cursor:pointer; transition:all 0.2s;">👎 ${rx.dislike || 0}</button>
            
            <button class="reply-toggle" style="background:none; border:none; color:#12a84e; font-weight:600; font-size:14px; margin-left:auto; cursor:pointer;">답글 달기</button>
        </div>
        
        <div class="reply-container" style="display:none; margin-top:15px; display:flex; gap:10px;">
            <input type="text" class="reply-input" placeholder="답글을 입력하세요..." style="flex-grow:1; padding:10px; font-size:14px; border:1px solid #ddd; border-radius:8px; outline:none;">
            <button class="reply-submit" style="background:#12a84e; color:#fff; font-weight:600; border:none; padding:0 16px; border-radius:8px; cursor:pointer;">등록</button>
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
      if (!entry.reactions) entry.reactions = { like: 0, dislike: 0 };
      entry.reactions[type] = (entry.reactions[type] || 0) + 1;
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
      entry.replies.push({ author: CURRENT_USER, content });
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
    reactions: { like: 0, dislike: 0 },
    replies: []
  });
  saveEntries(entries);
  closeModal();
  render();
});

render();
