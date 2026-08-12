let CURRENT_USER = '나';

// Load entries via API
async function loadEntries() {
  try {
    const payload = await apiRequest('/api/guestbook/', { method: 'GET' });
    return payload.data || [];
  } catch (error) {
    showToast(error.message, true);
    return [];
  }
}

let guestbookEntries = [];

const entryList = document.querySelector('#entry-list');
const entryCount = document.querySelector('#entry-count');
const emptyState = document.querySelector('#guestbook-empty');
const overlay = document.querySelector('#write-overlay');
const form = document.querySelector('#write-form');

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

async function render() {
  guestbookEntries = await loadEntries();
  const entries = guestbookEntries.slice();
  
  entryCount.textContent = `방명록 ${entries.length}개`;
  emptyState.hidden = entries.length > 0;

  entryList.innerHTML = entries
    .map(
      (entry) => {
        const rx = entry.reactions || { likedBy: [], dislikedBy: [] };
        const rp = entry.replies || [];
        
        const hasLiked = rx.likedBy.includes(CURRENT_USER);
        const hasDisliked = rx.dislikedBy.includes(CURRENT_USER);

        const repliesHtml = rp.map((r) => {
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
              <button class="reply-reaction-btn ${rHasLiked ? 'active-like' : ''}" data-type="like" data-reply-id="${r.id}">
                👍 ${rRx.likedBy.length > 0 ? rRx.likedBy.length : ''}
              </button>
              <button class="reply-reaction-btn ${rHasDisliked ? 'active-dislike' : ''}" data-type="dislike" data-reply-id="${r.id}">
                👎 ${rRx.dislikedBy.length > 0 ? rRx.dislikedBy.length : ''}
              </button>
            </div>
          </div>
        `}).join('');

        return `<article class="entry-card" data-id="${entry.id}">
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

entryList.addEventListener('click', async (event) => {
  const card = event.target.closest('.entry-card');
  if (!card) return;
  const id = parseInt(card.dataset.id, 10);
  
  // Delete
  if (event.target.closest('.entry-delete')) {
    if (!confirm('이 방명록을 삭제할까요?')) return;
    try {
      await apiRequest(`/api/guestbook/${id}`, { method: 'DELETE' });
      await render();
    } catch (err) {
      showToast(err.message, true);
    }
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
      try {
        await apiRequest(`/api/guestbook/${id}`, {
          method: 'PUT',
          body: JSON.stringify({ content: newContent })
        });
        await render();
      } catch (err) {
        showToast(err.message, true);
      }
    }
  }

  // Entry Reaction
  if (event.target.closest('.reaction-btn')) {
    const btn = event.target.closest('.reaction-btn');
    const type = btn.dataset.type;
    
    try {
      const payload = await apiRequest(`/api/guestbook/${id}/reaction`, {
        method: 'POST',
        body: JSON.stringify({ type })
      });
      
      const reactions = payload.data.reactions;
      
      // Update DOM directly instead of render() to prevent blinking
      const group = btn.closest('.reaction-group');
      const likeBtn = group.querySelector('[data-type="like"]');
      const dislikeBtn = group.querySelector('[data-type="dislike"]');
      
      const likeCount = reactions.likedBy.length;
      const dislikeCount = reactions.dislikedBy.length;
      
      likeBtn.className = `reaction-btn ${reactions.likedBy.includes(CURRENT_USER) ? 'active-like' : ''}`;
      likeBtn.innerHTML = `👍 좋아요 ${likeCount > 0 ? likeCount : ''}`;
      
      dislikeBtn.className = `reaction-btn ${reactions.dislikedBy.includes(CURRENT_USER) ? 'active-dislike' : ''}`;
      dislikeBtn.innerHTML = `👎 싫어요 ${dislikeCount > 0 ? dislikeCount : ''}`;
    } catch(err) {
      if (err.message) showToast(err.message, true);
    }
    return;
  }
  
  // Reply Reaction
  if (event.target.closest('.reply-reaction-btn')) {
    const btn = event.target.closest('.reply-reaction-btn');
    const type = btn.dataset.type;
    const replyId = parseInt(btn.dataset.replyId, 10);
    
    try {
      const payload = await apiRequest(`/api/guestbook/reply/${replyId}/reaction`, {
        method: 'POST',
        body: JSON.stringify({ type })
      });
      
      const reactions = payload.data.reactions;
      
      // Update DOM directly to prevent blinking
      const actionsDiv = btn.closest('.reply-actions');
      const likeBtn = actionsDiv.querySelector('[data-type="like"]');
      const dislikeBtn = actionsDiv.querySelector('[data-type="dislike"]');
      
      const likeCount = reactions.likedBy.length;
      const dislikeCount = reactions.dislikedBy.length;
      
      likeBtn.className = `reply-reaction-btn ${reactions.likedBy.includes(CURRENT_USER) ? 'active-like' : ''}`;
      likeBtn.innerHTML = `👍 ${likeCount > 0 ? likeCount : ''}`;
      
      dislikeBtn.className = `reply-reaction-btn ${reactions.dislikedBy.includes(CURRENT_USER) ? 'active-dislike' : ''}`;
      dislikeBtn.innerHTML = `👎 ${dislikeCount > 0 ? dislikeCount : ''}`;
    } catch(err) {
      if (err.message) showToast(err.message, true);
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
    try {
      await apiRequest(`/api/guestbook/${id}/reply`, {
        method: 'POST',
        body: JSON.stringify({ content })
      });
      await render();
    } catch(err) {
      showToast(err.message, true);
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

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const content = document.querySelector('#write-content').value.trim();
  if (!content) return;
  
  try {
    const btn = form.querySelector('.submit-btn');
    btn.disabled = true;
    await apiRequest('/api/guestbook/', {
      method: 'POST',
      body: JSON.stringify({ content })
    });
    closeModal();
    await render();
  } catch (err) {
    showToast(err.message, true);
  } finally {
    const btn = form.querySelector('.submit-btn');
    btn.disabled = false;
  }
});

// fetch user profile on load to know who CURRENT_USER is
apiRequest('/api/v1/auth/me', { method: 'GET' })
  .then(payload => {
    CURRENT_USER = payload.data.nickname;
    render();
  })
  .catch(() => {
    render(); // fallback
  });
