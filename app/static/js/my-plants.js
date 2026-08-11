const current=JSON.parse(localStorage.getItem('farmdaPlant')||'null');
let plants=JSON.parse(localStorage.getItem('farmdaPlants')||'[]');
if(current&&!plants.some(item=>item.name===current.name)){plants.push({...current,id:current.id||`plant-${Date.now()}`,energy:current.energy||0,stage:current.stage||'씨앗'});localStorage.setItem('farmdaPlants',JSON.stringify(plants));}
const list=document.querySelector('#my-plant-list');
const empty=document.querySelector('#empty-plants');
document.querySelector('#plant-count').textContent=plants.length;
document.querySelector('#bloom-count').textContent=plants.filter(item=>(item.energy||0)>=70).length;
if(!plants.length){empty.hidden=false;}else{
  plants.forEach((plant,index)=>{
    const energy=Math.max(0,Math.min(100,Number(plant.energy)||0));
    const stage=energy>=70?'꽃':energy>=40?'봉오리':energy>=20?'본잎':energy>=5?'떡잎':'씨앗';
    const card=document.createElement('article');card.className='plant-card';card.tabIndex=0;
    card.innerHTML=`<div class="plant-photo"><span>${plant.emoji||'🌱'}</span></div><div class="plant-body"><div class="plant-top"><div><small>PLANT ${String(index+1).padStart(2,'0')}</small><h2>${plant.name||'식물'}</h2></div><span class="stage-badge">${stage} 단계</span></div><div class="plant-energy"><span>성장 에너지</span><b>${energy} / 100</b></div><div class="energy-track"><i style="width:${energy}%"></i></div><div class="plant-enter"><span>상태창 들어가기</span><b>→</b></div></div>`;
    const open=()=>{localStorage.setItem('farmdaPlant',JSON.stringify(plant));location.href='dashboard-v2.html';};card.addEventListener('click',open);card.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();open();}});list.append(card);
  });
}
