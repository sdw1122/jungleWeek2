let lastAiEmotion = null;
let positive=0,negative=0;
let completionShown=false;
const messages=document.querySelector('#messages');
const stagePlant=document.querySelector('#seed');
const seedActions=document.querySelector('#seed-actions');
const chatForm=document.querySelector('#chat-form');
const chatInput=document.querySelector('#chat-input');
const chosen=JSON.parse(localStorage.getItem('farmdaPlant')||'null');
if(chosen){
    negative=Math.max(0,Math.min(100,Number(chosen.negativeEnergy)||0)); 
    positive=Math.max(0,Math.min(100,Number(chosen.positiveEnergy!==undefined?chosen.positiveEnergy:(chosen.energy||0)-negative)));
}
const prefixPattern=/^(이름 없음|무명|이름|이름없는 식물|이름모를|아무이름|없음|무)\s*/;
const plantName=chosen?chosen.name.replace(prefixPattern,''):'반려식물';
document.querySelector('#plant-name').textContent=plantName;
document.querySelector('.plant-chip h2').textContent=plantName;

const stages=[
  {min:0,name:'씨앗',emoji:'🌱',next:5,mood:'아직 흙 속에 있습니다. 물을 주세요!'},
  {min:5,name:'새싹',emoji:'🌿',next:20,mood:'작은 잎이 돋아났어요.'},
  {min:20,name:'유묘',emoji:'🪴',next:40,mood:'튼튼한 줄기와 잎사귀가 생겼어요.'},
  {min:40,name:'성목',emoji:'🌳',next:70,mood:'아주 크게 자라고 있어요.'},
  {min:70,name:'열매',emoji:'🍎',next:100,mood:'드디어 탐스러운 열매가 열렸어요!'}
];
const replies={water:'물주기완료! 촉촉해 졌어요. 💧',sun:'광합성중! 햇빛을 듬뿍 받고 있어요! ☀️',pet:'쓰담쓰담! 기분이 좋아요. ☺️',ignore:'조금 외로워요. 관심 좀 주세요. 😢'};

function updateGrowth(){
  const total=Math.min(100,positive+negative);
  const stage=[...stages].reverse().find(item=>total>=item.min);
  
  let currentStageName = stage.name;
  let currentEmoji = stage.emoji;
  let currentMood = stage.mood;

  if (negative > positive) {
      currentStageName = "흑화(" + stage.name + ")";
      currentEmoji = "🥀";
      currentMood = "불량하고 삐뚤어졌습니다.";
  }
  
  document.querySelector('#positive').textContent=positive;
  document.querySelector('#negative').textContent=negative;
  document.querySelector('#total').textContent=total;
  document.querySelector('#positive-bar').style.width=`${Math.min(100,positive)}%`;
  document.querySelector('#negative-bar').style.width=`${Math.min(100,negative)}%`;
  document.querySelector('#total-bar').style.width=`${total}%`;
  document.querySelector('#next').textContent=total>=100?'완료':Math.max(0,stage.next-total);
  document.querySelector('#stage-label').textContent=`${currentStageName} 단계`;
  document.querySelector('#mini-stage').textContent=currentEmoji;
  
  if (lastAiEmotion) {
      document.querySelector('#mood-copy').textContent = "현재 기분: " + lastAiEmotion;
  } else {
      document.querySelector('#mood-copy').textContent = currentMood;
  }
  
  if(chosen){
      chosen.energy=total;
      chosen.positiveEnergy=positive;
      chosen.negativeEnergy=negative;
      chosen.stage=stage.name;
      localStorage.setItem('farmdaPlant',JSON.stringify(chosen));
      const savedPlants=JSON.parse(localStorage.getItem('farmdaPlants')||'[]');
      const savedIndex=savedPlants.findIndex(item=>(item.id&&item.id===chosen.id)||item.name===chosen.name);
      if(savedIndex>=0){
          savedPlants[savedIndex]={...savedPlants[savedIndex],...chosen};
      }else{
          savedPlants.push(chosen);
      }
      localStorage.setItem('farmdaPlants',JSON.stringify(savedPlants));
  }
  
  const isSeed=total<5;
  seedActions.hidden=!isSeed;
  chatForm.hidden=isSeed;
  
  if(stagePlant.textContent!==currentEmoji){
      stagePlant.textContent=currentEmoji;
      stagePlant.animate([{transform:'scale(.5) rotate(-12deg)',opacity:.2},{transform:'scale(1.2) rotate(5deg)',opacity:1},{transform:'scale(1)'}],{duration:600,easing:'ease-out'});
  }
  
  if(total>=100&&!completionShown){
      completionShown=true;
      window.setTimeout(()=>{document.querySelector('#growth-modal').hidden=false;document.body.style.overflow='hidden';},500);
  }
}

document.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',()=>{
  const action=button.dataset.action;
  if(positive+negative>=100)return;
  if(action==='ignore')negative=Math.min(100,negative+5);else positive=Math.min(100,positive+5);
  messages.insertAdjacentHTML('beforeend',`<p class="user">${replies[action]}</p>`);
  messages.scrollTop=messages.scrollHeight;
  updateGrowth();
  stagePlant.animate([{transform:'scale(.94)'},{transform:'scale(1.08)'},{transform:'scale(1)'}],{duration:320});
}));

chatForm.addEventListener('submit', async event => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text || positive + negative >= 100) return;
  
  messages.insertAdjacentHTML('beforeend', '<p class="user">' + text.replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char])) + '</p>');
  chatInput.value = '';
  messages.scrollTop = messages.scrollHeight;
  
  try {
    const csrfRes = await fetch('/api/v1/auth/csrf');
    const csrfPayload = await csrfRes.json();
    const token = csrfPayload.data.csrfToken;

    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token
      },
      body: JSON.stringify({ plant_id: 1, message: text })
    });
    
    if (res.ok) {
      const data = await res.json();
      messages.insertAdjacentHTML('beforeend', '<p>' + data.response + '</p>');
      
      if (data.emotion) {
          lastAiEmotion = data.emotion;
      }
      
      if (data.sentiment === "POSITIVE") {
          positive = Math.min(100, positive + 1);
      } else if (data.sentiment === 'NEGATIVE') {
          negative = Math.min(100, negative + 1);
      }
    } else {
      messages.insertAdjacentHTML('beforeend', '<p>앗, 연결에 문제가 생겼어요.</p>');
    }
  } catch(e) {
    messages.insertAdjacentHTML('beforeend', '<p>Error: ' + e.message + '</p>');
  }
  
  messages.scrollTop = messages.scrollHeight;
  updateGrowth();
});

const profileToggle=document.querySelector('#profile-toggle');
const profileCard=document.querySelector('#profile-card');
profileToggle.addEventListener('click',()=>{
  const willOpen=profileCard.hidden;
  profileCard.hidden=!willOpen;
  profileToggle.setAttribute('aria-expanded',String(willOpen));
});
document.addEventListener('click',event=>{
  if(!profileCard.hidden&&!profileCard.contains(event.target)&&event.target!==profileToggle){
      profileCard.hidden=true;
      profileToggle.setAttribute('aria-expanded','false');
  }
});
updateGrowth();
const growthModal=document.querySelector('#growth-modal');
function closeGrowthModal(){growthModal.hidden=true;document.body.style.overflow='';}
document.querySelector('.modal-later').addEventListener('click',closeGrowthModal);
document.querySelector('.growth-modal-backdrop').addEventListener('click',closeGrowthModal);
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!growthModal.hidden)closeGrowthModal();});
