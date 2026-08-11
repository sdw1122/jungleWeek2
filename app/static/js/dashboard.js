let positive=0,negative=0;
let completionShown=false;
const messages=document.querySelector('#messages');
const stagePlant=document.querySelector('#seed');
const seedActions=document.querySelector('#seed-actions');
const chatForm=document.querySelector('#chat-form');
const chatInput=document.querySelector('#chat-input');
const chosen=JSON.parse(localStorage.getItem('farmdaPlant')||'null');
if(chosen){positive=Math.max(0,Math.min(100,Number(chosen.energy)||0));negative=Math.max(0,Math.min(100,Number(chosen.negativeEnergy)||0));}
const prefixPattern=/^(사랑을 담은|행운의|감사의|건강을 기원하는|싱그러운|우리의|존경의|사랑의)\s*/;
const plantName=chosen?chosen.name.replace(prefixPattern,''):'식물';
document.querySelector('#plant-name').textContent=plantName;
document.querySelector('.plant-chip h2').textContent=plantName;

const stages=[
  {min:0,name:'씨앗',emoji:'🌰',next:5,mood:'아직 싹을 틔우기 전입니다. 정성껏 돌봐주세요!'},
  {min:5,name:'떡잎',emoji:'🌱',next:20,mood:'작은 떡잎이 고개를 내밀었어요.'},
  {min:20,name:'본잎',emoji:'🪴',next:40,mood:'튼튼한 본잎이 자라며 생기가 넘쳐요.'},
  {min:40,name:'봉오리',emoji:'🌷',next:70,mood:'곧 꽃을 피울 봉오리가 맺혔어요.'},
  {min:70,name:'꽃',emoji:'🌸',next:100,mood:'정성 덕분에 아름다운 꽃이 피었어요!'}
];
const replies={water:'시원해요! 뿌리가 촉촉해졌어요. 💧',sun:'따뜻한 햇빛 덕분에 힘이 나요! ☀️',pet:'정성스러운 손길이 느껴져요. 🌱',ignore:'조금 외로워요. 저를 잊지 말아주세요. 🌧️'};

function updateGrowth(){
  const total=Math.min(100,positive+negative);
  const stage=[...stages].reverse().find(item=>total>=item.min);
  document.querySelector('#positive').textContent=positive;
  document.querySelector('#negative').textContent=negative;
  document.querySelector('#total').textContent=total;
  document.querySelector('#positive-bar').style.width=`${Math.min(100,positive)}%`;
  document.querySelector('#negative-bar').style.width=`${Math.min(100,negative)}%`;
  document.querySelector('#total-bar').style.width=`${total}%`;
  document.querySelector('#next').textContent=total>=100?'완료':Math.max(0,stage.next-total);
  document.querySelector('#stage-label').textContent=`${stage.name} 단계`;
  document.querySelector('#mini-stage').textContent=stage.emoji;
  document.querySelector('#mood-copy').textContent=positive>=negative?stage.mood:'관심이 조금 부족해요. 따뜻하게 돌봐주세요.';
  if(chosen){chosen.energy=total;chosen.negativeEnergy=negative;chosen.stage=stage.name;localStorage.setItem('farmdaPlant',JSON.stringify(chosen));const savedPlants=JSON.parse(localStorage.getItem('farmdaPlants')||'[]');const savedIndex=savedPlants.findIndex(item=>(item.id&&item.id===chosen.id)||item.name===chosen.name);if(savedIndex>=0){savedPlants[savedIndex]={...savedPlants[savedIndex],...chosen};}else{savedPlants.push(chosen);}localStorage.setItem('farmdaPlants',JSON.stringify(savedPlants));}
  const isSeed=total<5;
  seedActions.hidden=!isSeed;
  chatForm.hidden=isSeed;
  if(stagePlant.textContent!==stage.emoji){stagePlant.textContent=stage.emoji;stagePlant.animate([{transform:'scale(.5) rotate(-12deg)',opacity:.2},{transform:'scale(1.2) rotate(5deg)',opacity:1},{transform:'scale(1)'}],{duration:600,easing:'ease-out'});}
  if(total>=100&&!completionShown){completionShown=true;window.setTimeout(()=>{document.querySelector('#growth-modal').hidden=false;document.body.style.overflow='hidden';},500);}
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

const positiveWords=['사랑','예뻐','예쁘다','좋아','고마워','잘했어','힘내','행복','멋져','소중'];
const negativeWords=['싫어','미워','못생겼','바보','짜증','죽어','별로','안 예뻐'];
chatForm.addEventListener('submit',event=>{
  event.preventDefault();
  const text=chatInput.value.trim();
  if(!text||positive+negative>=100)return;
  const isNegative=negativeWords.some(word=>text.includes(word));
  const isPositive=positiveWords.some(word=>text.includes(word));
  if(isNegative&&!isPositive)negative=Math.min(100,negative+5);else positive=Math.min(100,positive+5);
  messages.insertAdjacentHTML('beforeend',`<p class="user">${text.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]))}</p>`);
  messages.insertAdjacentHTML('beforeend',`<p>${isNegative&&!isPositive?'조금 속상해요. 그래도 곁에 있어주세요. 🌧️':'따뜻한 말 고마워요! 마음이 쑥쑥 자라요. 🌱'}</p>`);
  chatInput.value='';
  messages.scrollTop=messages.scrollHeight;
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
  if(!profileCard.hidden&&!profileCard.contains(event.target)&&event.target!==profileToggle){profileCard.hidden=true;profileToggle.setAttribute('aria-expanded','false');}
});
updateGrowth();
const growthModal=document.querySelector('#growth-modal');
function closeGrowthModal(){growthModal.hidden=true;document.body.style.overflow='';}
document.querySelector('.modal-later').addEventListener('click',closeGrowthModal);
document.querySelector('.growth-modal-backdrop').addEventListener('click',closeGrowthModal);
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!growthModal.hidden)closeGrowthModal();});
