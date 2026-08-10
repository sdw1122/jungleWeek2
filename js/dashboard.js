let positive=0,negative=0;
const messages=document.querySelector('#messages');
const stagePlant=document.querySelector('#seed');
const chosen=JSON.parse(localStorage.getItem('farmdaPlant')||'null');
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
  if(stagePlant.textContent!==stage.emoji){stagePlant.textContent=stage.emoji;stagePlant.animate([{transform:'scale(.5) rotate(-12deg)',opacity:.2},{transform:'scale(1.2) rotate(5deg)',opacity:1},{transform:'scale(1)'}],{duration:600,easing:'ease-out'});}
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
updateGrowth();
