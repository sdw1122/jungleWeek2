import re

with open('app/static/js/dashboard.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Add lastAiEmotion at the top
if 'let lastAiEmotion = null;' not in content:
    content = 'let lastAiEmotion = null;\n' + content

# Fix updateGrowth
old_update_growth = r'''function updateGrowth\(\)\{
  const total=Math\.min\(100,positive\+negative\);
  const stage=\[\.\.\.stages\]\.reverse\(\)\.find\(item=>total>=item\.min\);
  document\.querySelector\('#positive'\)\.textContent=positive;
  document\.querySelector\('#negative'\)\.textContent=negative;
  document\.querySelector\('#total'\)\.textContent=total;
  document\.querySelector\('#positive-bar'\)\.style\.width=\$\{Math\.min\(100,positive\)\}%;
  document\.querySelector\('#negative-bar'\)\.style\.width=\$\{Math\.min\(100,negative\)\}%;
  document\.querySelector\('#total-bar'\)\.style\.width=\$\{total\}%;
  document\.querySelector\('#next'\)\.textContent=total>=100\?'완료':Math\.max\(0,stage\.next-total\);
  document\.querySelector\('#stage-label'\)\.textContent=\$\{stage\.name\} 단계;
  document\.querySelector\('#mini-stage'\)\.textContent=stage\.emoji;
  document\.querySelector\('#mood-copy'\)\.textContent=positive>=negative\?stage\.mood:'기분이 안 좋아요\. 잘해주세요\.';'''

new_update_growth = '''function updateGrowth(){
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
  document.querySelector('#positive-bar').style.width=${Math.min(100,positive)}%;
  document.querySelector('#negative-bar').style.width=${Math.min(100,negative)}%;
  document.querySelector('#total-bar').style.width=${total}%;
  document.querySelector('#next').textContent=total>=100?'완료':Math.max(0,stage.next-total);
  document.querySelector('#stage-label').textContent=${currentStageName} 단계;
  document.querySelector('#mini-stage').textContent=currentEmoji;
  
  if (lastAiEmotion) {
      document.querySelector('#mood-copy').textContent = "현재 기분: " + lastAiEmotion;
  } else {
      document.querySelector('#mood-copy').textContent = currentMood;
  }'''

content = re.sub(old_update_growth.replace('완료', '완료').replace('단계', '단계'), new_update_growth, content, flags=re.DOTALL)

# Fix stagePlant.textContent
content = content.replace('if(stagePlant.textContent!==stage.emoji){stagePlant.textContent=stage.emoji;', 'if(stagePlant.textContent!==currentEmoji){stagePlant.textContent=currentEmoji;')

# Fix chat handler AI emotion logic
# Previously I injected: document.getElementById('mood-copy').innerText = "현재 기분: " + data.emotion;
# I need to change it to: lastAiEmotion = data.emotion;
content = content.replace("document.getElementById('mood-copy').innerText = \"현재 기분: \" + data.emotion;", "lastAiEmotion = data.emotion;")

with open('app/static/js/dashboard.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Modification done.")
