const prefixPattern = /^(사랑을 담은|행운의|감사의|건강을 기원하는|싱그러운|우리의|존경의|사랑의)\s*/;
const list = document.querySelector('#my-plant-list');
const empty = document.querySelector('#empty-plants');

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));
}

function showError(message) {
  empty.hidden = false;
  empty.querySelector('h2').textContent = '식물 목록을 불러오지 못했어요';
  empty.querySelector('p').textContent = message;
  empty.querySelector('a').textContent = '다시 시도하기';
  empty.querySelector('a').href = 'my-plants.html';
}

function renderPlants(plants) {
  document.querySelector('#plant-count').textContent = plants.length;
  document.querySelector('#care-count').textContent = plants.filter(
    plant => plant.growthScore < 100
  ).length;
  document.querySelector('#bloom-count').textContent = plants.filter(
    plant => plant.growthScore >= 70
  ).length;

  if (!plants.length) {
    empty.hidden = false;
    return;
  }

  plants.forEach((plant, index) => {
    const energy = Math.max(0, Math.min(100, Number(plant.growthScore) || 0));
    const card = document.createElement('article');
    card.className = 'plant-card';
    card.tabIndex = 0;
    card.innerHTML = `<div class="plant-photo"></div><div class="plant-body"><div class="plant-top"><div><small>PLANT ${String(index + 1).padStart(2, '0')}</small><h2>${escapeHtml((plant.name || '식물').replace(prefixPattern, ''))}</h2></div><span class="stage-badge">${escapeHtml(plant.stageLabel)} 단계</span></div><div class="plant-energy"><span>성장 에너지</span><b>${energy} / 100</b></div><div class="energy-track"><i style="width:${energy}%"></i></div><div class="plant-enter"><span>상태창 들어가기</span><b>→</b></div></div>`;
    card.querySelector('.plant-photo').style.backgroundImage = plant.imageUrl
      ? `url("${plant.imageUrl}")`
      : '';
    const open = () => {
      location.href = `dashboard-v2.html?plantId=${plant.id}`;
    };
    card.addEventListener('click', open);
    card.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        open();
      }
    });
    list.append(card);
  });
}

async function loadPlants() {
  try {
    const response = await fetch('/api/v1/plants', { credentials: 'same-origin' });
    const payload = await response.json().catch(() => ({}));
    if (response.status === 401) {
      location.href = '/login.html?next=/my-plants.html';
      return;
    }
    if (!response.ok) {
      throw new Error(payload.error?.message || '잠시 후 다시 시도해 주세요.');
    }
    renderPlants(payload.data.plants);
  } catch (error) {
    showError(error.message);
  }
}

loadPlants();
