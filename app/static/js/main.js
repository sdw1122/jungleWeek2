const notice = document.querySelector('.notice');
const logoutButton = document.querySelector('#logout-button');

function showNotice(message) {
  notice.textContent = message;
  notice.classList.add('show');
  window.clearTimeout(showNotice.timer);
  showNotice.timer = window.setTimeout(() => notice.classList.remove('show'), 2200);
}

document.querySelectorAll('[data-coming]').forEach(button =>
  button.addEventListener('click', () => {
    showNotice('이 기능은 곧 만날 수 있어요. 준비 중입니다! 🌱');
  })
);

async function loadCurrentUser() {
  const response = await fetch('/api/v1/auth/me', { credentials: 'same-origin' });
  if (response.status === 401) {
    location.href = '/login.html?next=/main.html';
    return;
  }
  if (!response.ok) throw new Error('사용자 정보를 불러오지 못했습니다.');
  const payload = await response.json();
  const nickname = payload.data.user.nickname;
  logoutButton.textContent = nickname.slice(0, 1).toUpperCase();
  logoutButton.title = `${nickname} · 로그아웃`;
}

logoutButton.addEventListener('click', async () => {
  try {
    const csrfResponse = await fetch('/api/v1/auth/csrf', {
      credentials: 'same-origin'
    });
    const csrfPayload = await csrfResponse.json();
    const response = await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRF-Token': csrfPayload.data.csrfToken }
    });
    if (!response.ok) throw new Error('로그아웃하지 못했습니다.');
    location.href = '/login.html';
  } catch (error) {
    showNotice(error.message);
  }
});

loadCurrentUser().catch(error => showNotice(error.message));
