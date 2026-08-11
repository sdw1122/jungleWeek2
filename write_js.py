import codecs
content = '''const CURRENT_USER = '��';

function timeAgo(timestamp) {
  const diff = Math.max(0, Date.now() - timestamp);
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) return '���� ��';
  if (diff < hour) return Math.floor(diff / minute) + '�� ��';
  if (diff < day) return Math.floor(diff / hour) + 'õ�� ��';
  if (diff < day * 7) return Math.floor(diff / day) + '�� ��';
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

async function render() {
  try {
      const res = await fetch('/api/v1/guestbook');
      const data = await res.json();
      if (data.status === 'success') {
          const entries = data.data;
          entryCount.textContent = '�� ' + entries.length + '��';
          
          if (entries.length > 0) {
              emptyState.hidden = true;
          } else {
              emptyState.hidden = false;
          }

          entryList.innerHTML = entries
            .map(
              (entry) => `<article class="entry-card" data-id="${escapeHtml(entry.id.toString())}">
                <div class="entry-card-meta">
                  <span class="entry-author">${escapeHtml(entry.nicknameSnapshot)}</span>
                  <span>${timeAgo(new Date(entry.createdAt).getTime())}</span>
                </div>
                <p class="entry-content">${escapeHtml(entry.content)}</p>
              </article>`
            )
            .join('');
      }
  } catch (err) {
      console.error(err);
  }
}

function openModal() {
  overlay.hidden = false;
  setTimeout(() => {
    document.querySelector('#write-content').focus();
  }, 100);
}

function closeModal() {
  overlay.hidden = true;
  form.reset();
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
    const contentInput = document.querySelector('#write-content');
    if (!contentInput) return;
    const content = contentInput.value.trim();
    if (!content) return;
    
    try {
        const res = await fetch('/api/v1/guestbook', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });
        
        const data = await res.json();
        if (res.ok) {
            closeModal();
            render();
        } else {
            alert('pk���� �Ǻ�: ' + (data.error?.message || '������ ������ �̳� {������ �ϻ�Ǩ���ϴ�.'));
        }
    } catch (err) {
        alert('��Ư��Ÿ ������� ��ϻ�Ǩ���ϴ�.');
    }
  });
}

render();
'''
with codecs.open('app/static/js/guestbook.js', 'w', encoding='utf-8') as f:
    f.write(content)

