const tabs = document.querySelectorAll('.tab');
const views = document.querySelectorAll('.view');
const toast = document.querySelector('.toast');
const loginForm = document.querySelector('#login-form');
const signupForm = document.querySelector('#signup-form');
let csrfToken = '';

function show(name) {
  tabs.forEach(tab => tab.classList.toggle('active', tab.dataset.view === name));
  views.forEach(view => view.classList.toggle('active', view.id === name));
}

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle('error', isError);
  toast.classList.add('show');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove('show'), 2600);
}

function setBusy(form, busy) {
  const button = form.querySelector('button[type="submit"]');
  button.disabled = busy;
  button.setAttribute('aria-busy', String(busy));
}

async function loadCsrf() {
  const response = await fetch('/api/v1/auth/csrf', {
    credentials: 'same-origin'
  });
  if (!response.ok) throw new Error('로그인 보안 정보를 불러오지 못했습니다.');
  const payload = await response.json();
  csrfToken = payload.data.csrfToken;
}

async function apiRequest(path, options, retryCsrf = true) {
  if (!csrfToken) await loadCsrf();
  const response = await fetch(path, {
    ...options,
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken,
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));

  if (
    retryCsrf &&
    response.status === 403 &&
    payload.error?.code === 'CSRF_TOKEN_INVALID'
  ) {
    csrfToken = '';
    await loadCsrf();
    return apiRequest(path, options, false);
  }

  if (!response.ok) {
    const fieldMessage = payload.error?.fields
      ? Object.values(payload.error.fields)[0]
      : null;
    throw new Error(fieldMessage || payload.error?.message || '요청 처리에 실패했습니다.');
  }
  return payload;
}

tabs.forEach(tab => tab.addEventListener('click', () => show(tab.dataset.view)));
document.querySelectorAll('[data-switch]').forEach(button =>
  button.addEventListener('click', () => show(button.dataset.switch))
);

loginForm.addEventListener('submit', async event => {
  event.preventDefault();
  setBusy(loginForm, true);
  const form = new FormData(loginForm);
  try {
    const payload = await apiRequest('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email: form.get('email'),
        password: form.get('password'),
        remember: form.get('remember') === 'on'
      })
    });
    csrfToken = payload.data.csrfToken;
    showToast('로그인되었습니다. Farmda에 오신 것을 환영해요.');
    const next = new URLSearchParams(location.search).get('next');
    const destination = next && next.startsWith('/') && !next.startsWith('//')
      ? next
      : '/welcome.html';
    window.setTimeout(() => { location.href = destination; }, 450);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    setBusy(loginForm, false);
  }
});

signupForm.addEventListener('submit', async event => {
  event.preventDefault();
  setBusy(signupForm, true);
  const form = new FormData(signupForm);
  try {
    await apiRequest('/api/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify({
        nickname: form.get('nickname'),
        email: form.get('email'),
        password: form.get('password')
      })
    });
    const email = form.get('email');
    signupForm.reset();
    loginForm.elements.email.value = email;
    show('login');
    showToast('계정이 생성되었습니다. 로그인해 주세요.');
    loginForm.elements.password.focus();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    setBusy(signupForm, false);
  }
});

document.querySelector('.link').addEventListener('click', () => {
  showToast('비밀번호 찾기는 다음 단계에서 제공됩니다.');
});

const plant = document.querySelector('.plant');
const thumbnails = document.querySelectorAll('.thumbs button');
thumbnails.forEach(button => button.addEventListener('click', () => {
  plant.style.backgroundImage = `url("${button.dataset.image}")`;
  thumbnails.forEach(item => item.classList.toggle('active', item === button));
  plant.animate(
    [{ opacity: .55 }, { opacity: 1 }],
    { duration: 350, easing: 'ease-out' }
  );
}));

loadCsrf().catch(error => showToast(error.message, true));
