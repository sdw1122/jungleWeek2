const STORAGE_KEY = 'farmda_guestbook_entries';
const CURRENT_USER = '나'; // 현재 로그인한 내 닉네임 (실제 연동 시 세션에서 받아옴)

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
      author: '나',
      content: '식물 덕분에 아침마다 웃게 돼요. 다들 오늘도 좋은 하루 보내세요 🌱',
      createdAt: Date.now() - 1000 * 60 * 40,
      reactions: { likedBy: [], dislikedBy: [] },
      replies: []
    },
    {
      id: 'seed-2',
      author: '다육이엄마',
      content: 'Farmda에서 만난 인연 덕분에 식물 키우는 재미가 두 배가 됐어요. 감사합니다!',
      createdAt: Date.now() - 1000 * 60 * 60 * 5,
      reactions: { likedBy: [], dislikedBy: [] },
      replies: []
    },
    {
      id: 'seed-1',
      author: '초록정원사',
      content: '처음 시작할 땐 막막했는데 다들 응원해주셔서 여기까지 왔네요. 고맙습니다 :)',
      createdAt: Date.now() - 1000 * 60 * 60 * 27,
      reactions: { likedBy: [], dislikedBy: [] },
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
        const rx = entry.reactions || { likedBy: [], dislikedBy: [] };
        // Migration from old like/dislike format if needed
        if (typeof rx.like === 'number') { rx.likedBy = []; rx.dislikedBy = []; delete rx.like; delete rx.dislike; }
        
        const rp = entry.replies || [];
        
        const hasLiked = rx.likedBy.includes(CURRENT_USER);
        const hasDisliked = rx.dislikedBy.includes(CURRENT_USER);

        const repliesHtml = rp.map((r, index) => {
          const rRx = r.reactions || { likedBy: [], dislikedBy: [] };
          const rHasLiked = rRx.likedBy.includes(CURRENT_USER);
          const rHasDisliked = rRx.dislikedBy.includes(CURRENT_USER);
          
          return `
          <div class="reply-item">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
              <b class="reply-author">${escapeHtml(r.author)}</b>
            </div>
            <span class="reply-content">${escapeHtml(r.content)}</span>
            <div class="reply-actions">
              <button class="reply-reaction-btn ${rHasLiked ? 'active-like' : ''}" data-type="like" data-reply-index="${index}">
                👍 ${rRx.likedBy.length > 0 ? rRx.likedBy.length : ''}
              </button>
              <button class="reply-reaction-btn ${rHasDisliked ? 'active-dislike' : ''}" data-type="dislike" data-reply-index="${index}">
                👎 ${rRx.dislikedBy.length > 0 ? rRx.dislikedBy.length : ''}
              </button>
            </div>
          </div>
        `}).join('');

        return `<article class="entry-card" data-id="${escapeHtml(entry.id)}">
        <div class="entry-card-meta">
          <div class="avatar">${escapeHtml(entry.author).charAt(0)}</div>
          <strong class="entry-author">${escapeHtml(entry.author)}</strong>
          <span>${timeAgo(entry.createdAt)}</span>
          ${entry.author === CURRENT_USER ? `
            <div style="margin-left:auto; display:flex; gap:12px;">
              <button class="entry-edit" type="button" aria-label="수정">수정</button>
              <button class="entry-delete" type="button" aria-label="삭제">삭제</button>
            </div>
          ` : ''}
        </div>
        <p class="entry-content">${escapeHtml(entry.content)}</p>
        
        <div class="inline-edit-container">
          <textarea class="inline-edit-textarea">${escapeHtml(entry.content)}</textarea>
          <div class="inline-edit-actions">
            <button class="inline-btn-cancel">취소</button>
            <button class="inline-btn-save">저장</button>
          </div>
        </div>
        
        <div class="entry-actions">
            <div class="reaction-group">
              <button class="reaction-btn ${hasLiked ? 'active-like' : ''}" data-type="like">
                👍 좋아요 ${rx.likedBy.length > 0 ? rx.likedBy.length : ''}
              </button>
              <button class="reaction-btn ${hasDisliked ? 'active-dislike' : ''}" data-type="dislike">
                👎 싫어요 ${rx.dislikedBy.length > 0 ? rx.dislikedBy.length : ''}
              </button>
            </div>
            
            <button class="reply-toggle">
              <span>💬</span> 답글 달기
            </button>
        </div>
        
        <div class="reply-container">
            <input type="text" class="reply-input" placeholder="답글을 입력하세요...">
            <button class="reply-submit">등록</button>
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
  
  // Edit (Show Inline Form)
  if (event.target.closest('.entry-edit')) {
    const contentP = card.querySelector('.entry-content');
    const editContainer = card.querySelector('.inline-edit-container');
    
    contentP.style.display = 'none';
    editContainer.classList.add('active');
    editContainer.querySelector('.inline-edit-textarea').focus();
  }
  
  // Edit Cancel
  if (event.target.closest('.inline-btn-cancel')) {
    const contentP = card.querySelector('.entry-content');
    const editContainer = card.querySelector('.inline-edit-container');
    
    contentP.style.display = 'block';
    editContainer.classList.remove('active');
  }

  // Edit Save
  if (event.target.closest('.inline-btn-save')) {
    const newContent = card.querySelector('.inline-edit-textarea').value.trim();
    if (newContent) {
      const entries = loadEntries();
      const entry = entries.find(e => e.id === id);
      if (entry) {
        entry.content = newContent;
        saveEntries(entries);
        render();
      }
    }
  }

  // Entry Reaction
  if (event.target.closest('.reaction-btn')) {
    const type = event.target.closest('.reaction-btn').dataset.type;
    const entries = loadEntries();
    const entry = entries.find(e => e.id === id);
    if (entry) {
      if (!entry.reactions || typeof entry.reactions.like === 'number') {
        entry.reactions = { likedBy: [], dislikedBy: [] };
      }
      
      const targetArray = type === 'like' ? entry.reactions.likedBy : entry.reactions.dislikedBy;
      const otherArray = type === 'like' ? entry.reactions.dislikedBy : entry.reactions.likedBy;
      
      const index = targetArray.indexOf(CURRENT_USER);
      if (index > -1) {
        targetArray.splice(index, 1);
      } else {
        targetArray.push(CURRENT_USER);
        const otherIndex = otherArray.indexOf(CURRENT_USER);
        if (otherIndex > -1) otherArray.splice(otherIndex, 1);
      }
      
      saveEntries(entries);
      render();
    }
    return;
  }
  
  // Reply Reaction
  if (event.target.closest('.reply-reaction-btn')) {
    const btn = event.target.closest('.reply-reaction-btn');
    const type = btn.dataset.type;
    const replyIndex = parseInt(btn.dataset.replyIndex, 10);
    
    const entries = loadEntries();
    const entry = entries.find(e => e.id === id);
    if (entry && entry.replies && entry.replies[replyIndex]) {
      const reply = entry.replies[replyIndex];
      if (!reply.reactions) reply.reactions = { likedBy: [], dislikedBy: [] };
      
      const targetArray = type === 'like' ? reply.reactions.likedBy : reply.reactions.dislikedBy;
      const otherArray = type === 'like' ? reply.reactions.dislikedBy : reply.reactions.likedBy;
      
      const rIdx = targetArray.indexOf(CURRENT_USER);
      if (rIdx > -1) {
        targetArray.splice(rIdx, 1);
      } else {
        targetArray.push(CURRENT_USER);
        const otherIndex = otherArray.indexOf(CURRENT_USER);
        if (otherIndex > -1) otherArray.splice(otherIndex, 1);
      }
      
      saveEntries(entries);
      render();
    }
    return;
  }

  // Reply Toggle
  if (event.target.closest('.reply-toggle')) {
    const replyContainer = card.querySelector('.reply-container');
    replyContainer.classList.toggle('active');
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
      entry.replies.push({ 
        author: CURRENT_USER, 
        content,
        reactions: { likedBy: [], dislikedBy: [] }
      });
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
    reactions: { likedBy: [], dislikedBy: [] },
    replies: []
  });
  saveEntries(entries);
  closeModal();
  render();
});

render();
