const STORAGE_KEY = 'farmda_guestbook_entries';
const CURRENT_USER = '초록잎정민'; // 현재 로그인한 내 닉네임 (실제 연동 시 세션에서 받아옴)

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

        const repliesHtml = rp.map(r => `
          <div style="background:#f8f9fa; padding:12px 16px; margin-top:12px; border-radius:8px; border-left:3px solid #12a84e; font-size:14px; color:#333; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <b style="color:#222; margin-right:8px; display:inline-block; margin-bottom:4px;">${escapeHtml(r.author)}</b>
            <div style="line-height:1.5;">${escapeHtml(r.content)}</div>
          </div>
        `).join('');

        return `<article class="entry-card" data-id="${escapeHtml(entry.id)}" style="background:#fff; padding:24px; border-radius:16px; border:1px solid #eaeaea; margin-bottom:20px; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
        <div class="entry-card-meta" style="display:flex; align-items:center; margin-bottom:12px;">
          <div style="width:36px; height:36px; border-radius:50%; background:#e9ecef; display:flex; align-items:center; justify-content:center; margin-right:12px; font-weight:bold; color:#6c757d;">
             ${escapeHtml(entry.author).charAt(0)}
          </div>
          <strong class="entry-author" style="font-size:16px; color:#212529; margin-right:12px;">${escapeHtml(entry.author)}</strong>
          <span style="font-size:13px; color:#adb5bd;">${timeAgo(entry.createdAt)}</span>
          ${entry.author === CURRENT_USER ? `
            <div style="margin-left:auto; display:flex; gap:12px;">
              <button class="entry-edit" type="button" aria-label="수정" style="border:none;background:none;color:#6c757d;cursor:pointer;font-size:13px;font-weight:600;">수정</button>
              <button class="entry-delete" type="button" aria-label="삭제" style="border:none;background:none;color:#fa5252;cursor:pointer;font-size:13px;font-weight:600;">삭제</button>
            </div>
          ` : ''}
        </div>
        <p class="entry-content" style="font-size:15px; line-height:1.7; color:#343a40; margin:16px 0; word-break:break-all;">${escapeHtml(entry.content)}</p>
        
        <div style="display:flex; gap:10px; margin-top:20px; align-items:center; border-top:1px solid #f1f3f5; padding-top:16px;">
            <button class="reaction-btn" data-type="like" style="background:${hasLiked ? '#e3f2fd' : '#f8f9fa'}; color:${hasLiked ? '#1971c2' : '#495057'}; border:1px solid ${hasLiked ? '#a5d8ff' : '#dee2e6'}; border-radius:20px; padding:6px 14px; font-size:13px; font-weight:600; cursor:pointer; transition:all 0.2s;">
              👍 좋아요 ${rx.likedBy.length > 0 ? rx.likedBy.length : ''}
            </button>
            <button class="reaction-btn" data-type="dislike" style="background:${hasDisliked ? '#ffe3e3' : '#f8f9fa'}; color:${hasDisliked ? '#e03131' : '#495057'}; border:1px solid ${hasDisliked ? '#ffc9c9' : '#dee2e6'}; border-radius:20px; padding:6px 14px; font-size:13px; font-weight:600; cursor:pointer; transition:all 0.2s;">
              👎 싫어요 ${rx.dislikedBy.length > 0 ? rx.dislikedBy.length : ''}
            </button>
            
            <button class="reply-toggle" style="background:none; border:none; color:#12a84e; font-weight:700; font-size:14px; margin-left:auto; cursor:pointer; display:flex; align-items:center; gap:4px;">
              <span style="font-size:16px;">💬</span> 답글 달기
            </button>
        </div>
        
        <div class="reply-container" style="display:none; margin-top:16px; display:flex; gap:10px;">
            <input type="text" class="reply-input" placeholder="답글을 입력하세요..." style="flex-grow:1; padding:12px 16px; font-size:14px; border:1px solid #ced4da; border-radius:8px; outline:none; background:#f8f9fa; transition:border 0.2s;">
            <button class="reply-submit" style="background:#12a84e; color:#fff; font-weight:700; border:none; padding:0 20px; border-radius:8px; cursor:pointer; transition:background 0.2s;">등록</button>
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
      if (!entry.reactions || typeof entry.reactions.like === 'number') {
        entry.reactions = { likedBy: [], dislikedBy: [] };
      }
      
      const targetArray = type === 'like' ? entry.reactions.likedBy : entry.reactions.dislikedBy;
      const otherArray = type === 'like' ? entry.reactions.dislikedBy : entry.reactions.likedBy;
      
      const index = targetArray.indexOf(CURRENT_USER);
      if (index > -1) {
        // 이미 눌렀으면 취소
        targetArray.splice(index, 1);
      } else {
        // 안 눌렀으면 추가하고 반대편 취소
        targetArray.push(CURRENT_USER);
        const otherIndex = otherArray.indexOf(CURRENT_USER);
        if (otherIndex > -1) otherArray.splice(otherIndex, 1);
      }
      
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
    reactions: { likedBy: [], dislikedBy: [] },
    replies: []
  });
  saveEntries(entries);
  closeModal();
  render();
});

render();
