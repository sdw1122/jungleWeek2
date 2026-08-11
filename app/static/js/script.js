const tabs=document.querySelectorAll('.tab'),views=document.querySelectorAll('.view'),toast=document.querySelector('.toast');
function show(name){tabs.forEach(t=>t.classList.toggle('active',t.dataset.view===name));views.forEach(v=>v.classList.toggle('active',v.id===name))}
tabs.forEach(t=>t.addEventListener('click',()=>show(t.dataset.view)));document.querySelectorAll('[data-switch]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.switch)));
document.querySelector('#login-form').addEventListener('submit',event=>{event.preventDefault();toast.textContent='로그인되었습니다. Farmda에 오신 것을 환영해요.';toast.classList.add('show');setTimeout(()=>location.href='welcome.html',650)});
document.querySelector('#signup-form').addEventListener('submit',event=>{event.preventDefault();toast.textContent='계정이 생성되었습니다.';toast.classList.add('show');event.currentTarget.reset();setTimeout(()=>{toast.classList.remove('show');show('login')},900)});
const plant=document.querySelector('.plant'),thumbnails=document.querySelectorAll('.thumbs button');
thumbnails.forEach(button=>button.addEventListener('click',()=>{plant.style.backgroundImage=`url("${button.dataset.image}")`;thumbnails.forEach(item=>item.classList.toggle('active',item===button));plant.animate([{opacity:.55},{opacity:1}],{duration:350,easing:'ease-out'})}));
