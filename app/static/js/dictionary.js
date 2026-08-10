const plants=[
{name:'몬스테라',emoji:'🌿',category:'foliage',water:'흙 표면이 마르면 물주기 (봄~가을 7~10일, 겨울 10~14일 간격)',humidity:'50~60% 이상의 다습한 환경을 선호해요.',soil:'배수가 잘 되는 통기성 좋은 배양토(펄라이트 혼합)를 사용하세요.',light:'밝은 간접광을 좋아하며 직사광선은 피해주세요.',etc:'잎에 자연적으로 구멍(천공)이 생기는 것이 특징이며 공기정화 효과가 뛰어나요.'},
{name:'스투키',emoji:'🪴',category:'succulent',water:'흙이 완전히 마른 뒤 2~3주에 한 번 물을 주세요.',humidity:'건조한 실내 환경에도 잘 견뎌요.',soil:'배수가 매우 잘 되는 다육·선인장용 흙이 좋아요.',light:'밝은 빛을 좋아하지만 반음지에서도 잘 자라요.',etc:'공기정화 능력이 뛰어나고 관리가 매우 쉬워 초보자에게 추천해요.'},
{name:'산세베리아',emoji:'🌵',category:'succulent',water:'흙이 완전히 마른 뒤 2주에 한 번 정도 물을 주세요.',humidity:'건조한 실내 환경에 강해요.',soil:'배수가 잘 되는 사질토나 다육식물용 배양토를 사용하세요.',light:'약한 빛부터 강한 간접광까지 폭넓게 적응해요.',etc:'밤에도 산소를 배출하는 것으로 알려져 침실에 두기 좋아요.'},
{name:'스킨답서스',emoji:'🍃',category:'foliage',water:'흙 표면이 마르면 7일 전후로 물을 주세요.',humidity:'보통 습도에서 잘 자라고 건조에도 강해요.',soil:'배수가 잘 되는 일반 배양토면 충분해요.',light:'밝은 간접광부터 반음지까지 폭넓게 적응해요.',etc:'덩굴성으로 잘 늘어지고 수경재배도 가능해 번식이 쉬워요.'},
{name:'아레카야자',emoji:'🌴',category:'palm',water:'흙 표면이 살짝 마르면 7일 전후로 물을 주고, 여름엔 더 자주 주세요.',humidity:'50% 이상의 높은 습도를 좋아해요. 잎에 분무해주면 좋아요.',soil:'배수가 잘 되는 부엽토 혼합 배양토를 사용하세요.',light:'밝은 간접광이 적당해요.',etc:'대표적인 공기정화 식물로 실내 습도 유지에도 효과적이에요.'},
{name:'파키라',emoji:'🌳',category:'palm',water:'흙이 마른 뒤 7~10일에 한 번 물을 주세요.',humidity:'보통 습도에서 무난하게 적응해요.',soil:'배수가 잘 되는 일반 배양토를 사용하세요.',light:'밝은 간접광이 좋고 약한 직사광선도 견뎌요.',etc:'money tree라 불리며 줄기를 땋아 재배하는 경우가 많고 생명력이 강해요.'},
{name:'고무나무',emoji:'🌱',category:'foliage',water:'흙 표면이 마르면 7~10일 간격으로 물을 주세요.',humidity:'보통 습도에서 잘 자라요.',soil:'배수가 잘 되는 비옥한 배양토가 좋아요.',light:'밝은 간접광을 좋아해요.',etc:'크고 두꺼운 잎이 특징이며 잎의 먼지를 닦아주면 광택과 광합성에 도움돼요.'},
{name:'스파티필름',emoji:'🌼',category:'flower',water:'흙 표면이 마르면 5~7일 간격으로 물을 주세요. 잎이 처지면 물 부족 신호예요.',humidity:'높은 습도를 좋아해요.',soil:'배수가 잘 되면서 유기물이 풍부한 배양토가 좋아요.',light:'반음지부터 밝은 간접광까지 낮은 광량에서도 개화해요.',etc:'흰 꽃(불염포)이 피는 대표적인 공기정화 식물이에요.'},
{name:'아이비',emoji:'🍃',category:'etc',water:'흙 표면이 마르면 5~7일 간격으로 물을 주세요.',humidity:'다습한 환경을 선호해요.',soil:'배수가 잘 되는 일반 배양토를 사용하세요.',light:'밝은 간접광부터 반음지까지 잘 적응해요.',etc:'덩굴성으로 벽이나 트렐리스를 타고 자라며 공기정화 효과가 우수해요.'},
{name:'필로덴드론',emoji:'🌿',category:'foliage',water:'흙 표면이 마르면 7일 전후로 물을 주세요.',humidity:'높은 습도에서 잘 자라요.',soil:'배수가 잘 되는 유기물이 풍부한 배양토가 좋아요.',light:'밝은 간접광이 적당해요.',etc:'하트 모양의 잎이 매력적이며 덩굴형·직립형 등 품종이 다양해요.'},
{name:'테이블야자',emoji:'🌴',category:'palm',water:'흙 표면이 마르면 7일 전후로 물을 주세요.',humidity:'높은 습도를 좋아해요.',soil:'배수가 잘 되는 배양토를 사용하세요.',light:'반음지에서도 잘 자라며 강한 직사광선은 피해주세요.',etc:'낮은 광량에도 강해 실내 어디에나 두기 좋은 소형 야자예요.'},
{name:'알로에',emoji:'🪴',category:'succulent',water:'흙이 완전히 마른 뒤 2~3주에 한 번 물을 주세요.',humidity:'건조한 환경을 선호해요.',soil:'배수가 매우 잘 되는 다육·선인장용 흙이 좋아요.',light:'밝은 직사광선부터 간접광까지 잘 견뎌요.',etc:'잎 속 젤은 피부 진정 등에 활용되며 관리가 쉬운 다육식물이에요.'},
{name:'선인장',emoji:'🌵',category:'succulent',water:'흙이 완전히 마른 뒤 2~4주에 한 번, 겨울엔 더 줄여서 물을 주세요.',humidity:'매우 건조한 환경을 선호해요.',soil:'배수가 뛰어난 선인장 전용 흙을 사용하세요.',light:'강한 직사광선을 좋아해요.',etc:'과습에 약해 뿌리가 쉽게 썩으므로 물 주는 간격 조절이 가장 중요해요.'},
{name:'페페로미아',emoji:'🍀',category:'flower',water:'흙 표면이 마르면 7~10일 간격으로 물을 주세요.',humidity:'보통~높은 습도에서 잘 자라요.',soil:'배수가 잘 되는 가벼운 배양토가 좋아요.',light:'밝은 간접광이 적당해요.',etc:'통통한 잎에 수분을 저장해 물 관리에 대한 내성이 강하고 크기가 작아 공간 활용이 좋아요.'},
{name:'행운목',emoji:'🎍',category:'palm',water:'흙 표면이 마르면 7~10일 간격으로 물을 주세요.',humidity:'보통 습도에서 잘 적응해요.',soil:'배수가 잘 되는 일반 배양토를 사용하세요.',light:'밝은 간접광부터 반음지까지 무난해요.',etc:'이름처럼 행운을 상징해 개업·이사 선물로 인기가 많고 향긋한 꽃이 피기도 해요.'},
{name:'벤자민고무나무',emoji:'🌳',category:'foliage',water:'흙 표면이 마르면 7일 전후로 물을 주세요.',humidity:'보통~높은 습도를 선호해요.',soil:'배수가 잘 되는 비옥한 배양토가 좋아요.',light:'밝은 간접광이 적당해요.',etc:'환경 변화(이동, 온도차)에 민감해 낙엽이 생길 수 있어 자리를 자주 옮기지 않는 게 좋아요.'},
{name:'칼라데아',emoji:'🌿',category:'flower',water:'흙 표면이 마르지 않도록 5~7일 간격으로 물을 주세요.',humidity:'60% 이상의 매우 높은 습도가 필요해요.',soil:'배수가 잘 되면서도 수분 보유력 있는 배양토가 좋아요.',light:'반음지가 적당하며 직사광선은 피해주세요.',etc:'낮과 밤에 잎을 접었다 펴는 수면 운동을 하는 독특한 습성과 화려한 잎 무늬가 특징이에요.'},
{name:'드라세나',emoji:'🪴',category:'foliage',water:'흙 표면이 마르면 7~10일 간격으로 물을 주세요.',humidity:'보통 습도에서 잘 적응해요.',soil:'배수가 잘 되는 일반 배양토를 사용하세요.',light:'밝은 간접광부터 반음지까지 무난해요.',etc:'품종이 다양하고 관리가 쉬워 초보자에게 적합하며 공기정화 효과가 좋아요.'},
{name:'호야',emoji:'🌸',category:'succulent',water:'흙이 마른 뒤 10~14일에 한 번 물을 주세요.',humidity:'보통~높은 습도를 선호해요.',soil:'배수가 매우 잘 되는 배양토를 사용하세요.',light:'밝은 간접광이 좋으며 약간의 직사광선은 개화에 도움돼요.',etc:'별 모양의 왁스 질감 꽃이 피며 덩굴성이라 행잉플랜트로 인기가 많아요.'},
{name:'아디안텀',emoji:'🌾',category:'etc',water:'흙이 항상 촉촉하도록 3~4일 간격으로 자주 물을 주세요.',humidity:'60% 이상의 매우 높은 습도가 필요해요.',soil:'배수가 잘 되면서 수분 보유력이 좋은 배양토가 좋아요.',light:'반음지가 적당하며 직사광선은 피해주세요.',etc:'건조에 매우 민감해 잎이 쉽게 마르므로 습도 관리가 까다롭지만 섬세한 잎 모양이 매력적이에요.'}
];
const grid=document.querySelector('#dict-grid'),overlay=document.querySelector('#dict-overlay'),search=document.querySelector('#dict-search'),empty=document.querySelector('#dict-empty'),filters=document.querySelectorAll('.dict-filter');let category='all';
grid.innerHTML=plants.map((plant,index)=>`<button class="dict-card" data-index="${index}" data-name="${plant.name.toLowerCase()}" data-category="${plant.category}"><span class="dict-emoji">${plant.emoji}</span><h2>${plant.name}</h2></button>`).join('');
const cards=[...grid.querySelectorAll('.dict-card')];
function openDetail(plant){document.querySelector('#detail-emoji').textContent=plant.emoji;document.querySelector('#detail-name').textContent=plant.name;document.querySelector('#detail-water').textContent=plant.water;document.querySelector('#detail-humidity').textContent=plant.humidity;document.querySelector('#detail-soil').textContent=plant.soil;document.querySelector('#detail-light').textContent=plant.light;document.querySelector('#detail-etc').textContent=plant.etc;overlay.hidden=false}
function closeDetail(){overlay.hidden=true}
function filterCards(){const term=search.value.trim().toLowerCase();let count=0;cards.forEach(card=>{const visible=(category==='all'||card.dataset.category===category)&&card.dataset.name.includes(term);card.hidden=!visible;if(visible)count++});empty.hidden=count>0}
cards.forEach(card=>card.addEventListener('click',()=>openDetail(plants[card.dataset.index])));
search.addEventListener('input',filterCards);
filters.forEach(button=>button.addEventListener('click',()=>{category=button.dataset.filter;filters.forEach(item=>item.classList.toggle('active',item===button));filterCards()}));
document.querySelector('#dict-close').addEventListener('click',closeDetail);
overlay.addEventListener('click',event=>{if(event.target===overlay)closeDetail()});
document.addEventListener('keydown',event=>{if(event.key==='Escape')closeDetail()});
