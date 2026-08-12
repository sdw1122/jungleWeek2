(() => {
  const profile = document.querySelector('.farmada-global-profile');
  if (!profile) return;

  const toggle = profile.querySelector('.farmada-profile-button');
  const menu = profile.querySelector('.farmada-profile-menu');
  const logout = profile.querySelector('[data-global-logout]');

  function setOpen(open) {
    menu.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
  }

  toggle.addEventListener('click', () => setOpen(menu.hidden));
  document.addEventListener('click', event => {
    if (!profile.contains(event.target)) setOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') setOpen(false);
  });
  logout.addEventListener('click', async () => {
    logout.disabled = true;
    try {
      const csrfResponse = await fetch('/api/v1/auth/csrf', { credentials: 'same-origin' });
      const csrfPayload = await csrfResponse.json();
      const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRF-Token': csrfPayload.data.csrfToken }
      });
      if (!response.ok) throw new Error('로그아웃하지 못했습니다.');
      location.href = '/login.html';
    } catch (error) {
      logout.disabled = false;
      window.alert(error.message);
    }
  });
})();
