const today=new Date();
document.querySelector('#entry-date').textContent=today.toLocaleDateString('ko-KR',{year:'numeric',month:'long',day:'numeric'});
document.querySelector('.new-entry').addEventListener('click',()=>{
  const toast=document.querySelector('.toast');
  toast.textContent='일기 작성 기능은 백엔드 연결 후 제공될 예정입니다. 🌱';
  toast.classList.add('show');
  setTimeout(()=>toast.classList.remove('show'),2300);
});
