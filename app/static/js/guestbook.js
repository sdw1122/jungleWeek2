let currentUserId = null;
let csrfToken = '';
let editingEntryId = null;

async function initUser() {
  try {
    const res = await fetch('/api/v1/auth/me', { credentials: 'same-origin' });
    const payload = await res.json();
    if (payload.data && payload.data.user) {
      currentUserId = payload.data.user.id;
    }
  } catch(e) {
    console.error('Failed to load user', e);
  }
}

async function loadCsrf() {
  try {
    const response = await fetch('/api/v1/auth/csrf', { credentials: 'same-origin' });
    const payload = await response.json();
    csrfToken = payload.data.csrfToken;
  } catch (e) {
    console.error('Failed to load CSRF token', e);
  }
}

function timeAgo(timestamp) {
  const diff = Math.max(0, Date.now() - timestamp);
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) return '방금 전';
  if (diff < hour) return Math.floor(diff / minute) + '분 전';
  if (diff < day) return Math.floor(diff / hour) + '시간 전';
  if (diff < day * 7) return Math.floor(diff / day) + '일 전';
  return new Date(timestamp).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

const entryList = document.querySelector('#entry-list');
const entryCount = document.querySelector('#entry-count');
const emptyState = document.querySelector('#guestbook-empty');
const overlay = document.querySelector('#write-overlay');
const form = document.querySelector('#write-form');
const openWriteBtn = document.querySelector('#open-write');
const writeCloseBtn = document.querySelector('#write-close');
const writeCancelBtn = document.querySelector('#write-cancel');
const writeTitle = document.querySelector('#write-overlay h2');
const writeContentInput = document.querySelector('#write-content');

async function render() {
  try {
      const res = await fetch('/api/v1/guestbook');
      const data = await res.json();
      if (data.status === 'success') {
          const entries = data.data;
          entryCount.textContent = '총 ' + entries.length + '개';
          
          if (entries.length > 0) {
              emptyState.hidden = true;
          } else {
              emptyState.hidden = false;
          }

          entryList.innerHTML = entries
            .map(
              (entry) => {
                let actionHtml = '';
                if (currentUserId && entry.authorUserId === currentUserId) {
                  actionHtml = `
                    <div class="entry-actions">
                      <button type="button" class="action-btn edit-btn" onclick="openEditModal(${entry.id}, '${escapeHtml(entry.content).replace(/'/g, "\\'")}')">수정</button>
                      <button type="button" class="action-btn delete-btn" onclick="deleteEntry(${entry.id})">삭제</button>
                    </div>
                  `;
                }

                return `<article class="entry-card" data-id="${escapeHtml(entry.id.toString())}">
                  <div class="entry-card-meta">
                    <span class="entry-author">${escapeHtml(entry.nicknameSnapshot)}</span>
                    <span>${timeAgo(new Date(entry.createdAt).getTime())}</span>
                    ${actionHtml}
                  </div>
                  <p class="entry-content">${escapeHtml(entry.content)}</p>
                </article>`;
              }
            )
            .join('');
      }
  } catch (err) {
      console.error(err);
  }
}

function openModal() {
  editingEntryId = null;
  if(writeTitle) writeTitle.textContent = '방명록 작성';
  if(form) form.reset();
  overlay.hidden = false;
  setTimeout(() => {
    if(writeContentInput) writeContentInput.focus();
  }, 100);
}

window.openEditModal = function(id, currentContent) {
  editingEntryId = id;
  if(writeTitle) writeTitle.textContent = '방명록 수정';
  if(writeContentInput) writeContentInput.value = currentContent;
  overlay.hidden = false;
  setTimeout(() => {
    if(writeContentInput) writeContentInput.focus();
  }, 100);
}

window.deleteEntry = async function(id) {
  if (!confirm('정말 삭제하시겠습니까?')) return;
  
  try {
    const res = await fetch('/api/v1/guestbook/' + id, {
        method: 'DELETE',
        headers: { 
            'X-CSRF-Token': csrfToken
        },
        credentials: 'same-origin'
    });
    const data = await res.json();
    if (res.ok) {
        render();
    } else {
        alert('삭제 실패: ' + (data.error?.message || '권한이 없거나 오류가 발생했습니다.'));
    }
  } catch (err) {
      alert('네트워크 오류가 발생했습니다.');
  }
}

function closeModal() {
  overlay.hidden = true;
  if(form) form.reset();
  editingEntryId = null;
}

if (openWriteBtn) {
  openWriteBtn.addEventListener('click', openModal);
}
if (writeCloseBtn) {
  writeCloseBtn.addEventListener('click', closeModal);
}
if (writeCancelBtn) {
  writeCancelBtn.addEventListener('click', closeModal);
}

if (overlay) {
  overlay.addEventListener('click', (event) => {
    if (event.target === overlay) closeModal();
  });
}

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && overlay && !overlay.hidden) closeModal();
});

if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!writeContentInput) return;
    const content = writeContentInput.value.trim();
    if (!content) return;
    
    try {
        const method = editingEntryId ? 'PUT' : 'POST';
        const url = editingEntryId ? ('/api/v1/guestbook/' + editingEntryId) : '/api/v1/guestbook';
        
        const res = await fetch(url, {
            method: method,
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            credentials: 'same-origin',
            body: JSON.stringify({ content: content })
        });
        
        const data = await res.json();
        if (res.ok) {
            closeModal();
            render();
        } else {
            alert('작성 실패: ' + (data.error?.message || '권한이 없거나 오류가 발생했습니다.'));
        }
    } catch (err) {
        alert('네트워크 오류가 발생했습니다.');
    }
  });
}

// Initialize
(async function init() {
  await Promise.all([initUser(), loadCsrf()]);
  render();
})();
