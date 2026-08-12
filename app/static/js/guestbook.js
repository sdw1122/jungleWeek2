let currentUser = null;
let csrfToken = '';
let guestbookEntries = [];

const entryList = document.querySelector('#entry-list');
const entryCount = document.querySelector('#entry-count');
const emptyState = document.querySelector('#guestbook-empty');
const overlay = document.querySelector('#write-overlay');
const form = document.querySelector('#write-form');

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
}

function timeAgo(timestamp) {
  const diff = Math.max(0, Date.now() - Number(timestamp));
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) return '방금 전';
  if (diff < hour) return `${Math.floor(diff / minute)}분 전`;
  if (diff < day) return `${Math.floor(diff / hour)}시간 전`;
  if (diff < day * 7) return `${Math.floor(diff / day)}일 전`;
  return new Date(Number(timestamp)).toLocaleDateString('ko-KR', {
    year: 'numeric', month: 'long', day: 'numeric'
  });
}

function showError(message) {
  window.alert(message);
}

async function loadSession() {
  const [meResponse, csrfResponse] = await Promise.all([
    fetch('/api/v1/auth/me', { credentials: 'same-origin' }),
    fetch('/api/v1/auth/csrf', { credentials: 'same-origin' })
  ]);
  const me = await meResponse.json().catch(() => ({}));
  const csrf = await csrfResponse.json().catch(() => ({}));
  currentUser = me.data?.user || null;
  csrfToken = csrf.data?.csrfToken || '';
}

async function apiRequest(path, options = {}) {
  const method = String(options.method || 'GET').toUpperCase();
  const mutating = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);
  const response = await fetch(path, {
    ...options,
    method,
    credentials: 'same-origin',
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(mutating ? { 'X-CSRF-Token': csrfToken } : {}),
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (response.status === 401) {
    location.href = `/login.html?next=${encodeURIComponent(location.pathname)}`;
    throw new Error('로그인이 필요합니다.');
  }
  if (!response.ok) {
    throw new Error(payload.error?.message || payload.message || '요청을 처리하지 못했습니다.');
  }
  return payload;
}

async function loadEntries() {
  const payload = await apiRequest('/api/v1/guestbook');
  return payload.data || [];
}

function reactionButtons(reactions, className, replyId = null) {
  const likedBy = reactions?.likedBy || [];
  const dislikedBy = reactions?.dislikedBy || [];
  const nickname = currentUser?.nickname;
  const replyAttribute = replyId ? ` data-reply-id="${replyId}"` : '';
  return `<button type="button" class="${className} ${likedBy.includes(nickname) ? 'active-like' : ''}" data-type="like"${replyAttribute}>👍 ${className === 'reaction-btn' ? '좋아요 ' : ''}${likedBy.length || ''}</button>
    <button type="button" class="${className} ${dislikedBy.includes(nickname) ? 'active-dislike' : ''}" data-type="dislike"${replyAttribute}>👎 ${className === 'reaction-btn' ? '싫어요 ' : ''}${dislikedBy.length || ''}</button>`;
}

function replyMarkup(reply) {
  return `<div class="reply-item">
    <div class="reply-heading"><b class="reply-author">${escapeHtml(reply.author)}</b><span>${timeAgo(reply.createdAt)}</span></div>
    <span class="reply-content">${escapeHtml(reply.content)}</span>
    <div class="reply-actions">${reactionButtons(reply.reactions, 'reply-reaction-btn', reply.id)}</div>
  </div>`;
}

function entryMarkup(entry) {
  const isOwner = entry.authorUserId === currentUser?.id;
  return `<article class="entry-card" data-id="${entry.id}">
    <div class="entry-card-meta">
      <div class="avatar">${escapeHtml(entry.author).charAt(0)}</div>
      <strong class="entry-author">${escapeHtml(entry.author)}</strong>
      <span>${timeAgo(entry.createdAt)}</span>
      ${isOwner ? '<div class="owner-actions"><button class="entry-edit" type="button">수정</button><button class="entry-delete" type="button">삭제</button></div>' : ''}
    </div>
    <p class="entry-content">${escapeHtml(entry.content)}</p>
    <div class="inline-edit-container">
      <textarea class="inline-edit-textarea" maxlength="500">${escapeHtml(entry.content)}</textarea>
      <div class="inline-edit-actions"><button class="inline-btn-cancel" type="button">취소</button><button class="inline-btn-save" type="button">저장</button></div>
    </div>
    <div class="entry-actions">
      <div class="reaction-group">${reactionButtons(entry.reactions, 'reaction-btn')}</div>
      <button class="reply-toggle" type="button"><span>💬</span> 답글 달기</button>
    </div>
    <div class="reply-container"><input type="text" class="reply-input" maxlength="500" placeholder="답글을 입력하세요..."><button class="reply-submit" type="button">등록</button></div>
    <div class="reply-list">${(entry.replies || []).map(replyMarkup).join('')}</div>
  </article>`;
}

async function render() {
  try {
    guestbookEntries = await loadEntries();
    entryCount.textContent = `방명록 ${guestbookEntries.length}개`;
    emptyState.hidden = guestbookEntries.length > 0;
    entryList.innerHTML = guestbookEntries.map(entryMarkup).join('');
  } catch (error) {
    entryList.innerHTML = `<p class="guestbook-error">${escapeHtml(error.message)}</p>`;
  }
}

entryList.addEventListener('click', async event => {
  const card = event.target.closest('.entry-card');
  if (!card) return;
  const entryId = Number(card.dataset.id);

  if (event.target.closest('.entry-edit')) {
    card.querySelector('.entry-content').hidden = true;
    card.querySelector('.inline-edit-container').classList.add('active');
    card.querySelector('.inline-edit-textarea').focus();
    return;
  }
  if (event.target.closest('.inline-btn-cancel')) {
    card.querySelector('.entry-content').hidden = false;
    card.querySelector('.inline-edit-container').classList.remove('active');
    return;
  }
  if (event.target.closest('.reply-toggle')) {
    card.querySelector('.reply-container').classList.toggle('active');
    return;
  }

  try {
    if (event.target.closest('.entry-delete')) {
      if (!window.confirm('이 방명록을 삭제할까요?')) return;
      await apiRequest(`/api/v1/guestbook/${entryId}`, { method: 'DELETE' });
    } else if (event.target.closest('.inline-btn-save')) {
      const content = card.querySelector('.inline-edit-textarea').value.trim();
      if (!content) return;
      await apiRequest(`/api/v1/guestbook/${entryId}`, {
        method: 'PUT', body: JSON.stringify({ content })
      });
    } else if (event.target.closest('.reaction-btn')) {
      const button = event.target.closest('.reaction-btn');
      await apiRequest(`/api/v1/guestbook/${entryId}/reaction`, {
        method: 'POST', body: JSON.stringify({ type: button.dataset.type })
      });
    } else if (event.target.closest('.reply-reaction-btn')) {
      const button = event.target.closest('.reply-reaction-btn');
      await apiRequest(`/api/v1/guestbook/reply/${button.dataset.replyId}/reaction`, {
        method: 'POST', body: JSON.stringify({ type: button.dataset.type })
      });
    } else if (event.target.closest('.reply-submit')) {
      const content = card.querySelector('.reply-input').value.trim();
      if (!content) return;
      await apiRequest(`/api/v1/guestbook/${entryId}/reply`, {
        method: 'POST', body: JSON.stringify({ content })
      });
    } else {
      return;
    }
    await render();
  } catch (error) {
    showError(error.message);
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
overlay.addEventListener('click', event => {
  if (event.target === overlay) closeModal();
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !overlay.hidden) closeModal();
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  const content = document.querySelector('#write-content').value.trim();
  if (!content) return;
  const button = form.querySelector('.submit-btn');
  button.disabled = true;
  try {
    await apiRequest('/api/v1/guestbook', {
      method: 'POST', body: JSON.stringify({ content })
    });
    closeModal();
    await render();
  } catch (error) {
    showError(error.message);
  } finally {
    button.disabled = false;
  }
});

(async function init() {
  await loadSession();
  await render();
})();
