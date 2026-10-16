(() => {
  const $ = (s) => document.querySelector(s);
  const Agent = window.RequirementAgent;
  const messages = $('#messages'), input = $('#user-input'), send = $('#send-button');
  const welcome = $('#welcome-block'), progressFill = $('#progress-fill'), progressCount = $('#progress-count');
  const fields = [
    {key:'users',label:'目标用户',choices:['内部员工','客户 / 用户','管理员','不确定，先帮我梳理']},
    {key:'pain',label:'核心痛点',choices:['信息分散，找起来麻烦','流程太多，效率低','容易遗漏或出错','其他 / 我来描述']},
    {key:'outcome',label:'预期结果',choices:['节省处理时间','减少错误或遗漏','体验更清晰顺畅','其他 / 我来描述']},
    {key:'flow',label:'关键流程',choices:['创建 / 提交一项内容','查询 / 查看信息','审批 / 跟进任务','其他 / 我来描述']},
    {key:'scope',label:'范围与限制',choices:['暂时没有明确限制','需要权限控制','需要连接现有系统','还没想好，列为待确认']},
    {key:'acceptance',label:'成功标准',choices:['完成时间变短','错误 / 遗漏变少','用户可以独立完成','暂时没有标准，帮我建议']}
  ];
  const state={started:false,initial:'',domain:null,index:0,answers:{},questions:[],done:false,pendingClarification:null,followed:{},supplements:[]};
  document.querySelectorAll('.suggestion').forEach(b=>b.addEventListener('click',()=>begin(b.dataset.prompt)));
  function escapeHtml(str=''){return String(str).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function addMessage(text,role='assistant',label=''){
    const el=document.createElement('div');el.className=`message ${role}`;
    el.innerHTML=`<div class="message-avatar">${role==='assistant'?'译':'U'}</div><div>${label?`<div class="question-label">${escapeHtml(label)}</div>`:''}<div class="bubble">${escapeHtml(text)}</div></div>`;
    messages.appendChild(el);$('#chat-area').scrollTop=$('#chat-area').scrollHeight;
  }
  function doneCount(){return Object.keys(state.answers).length;}
  function setProgress(){
    const total=state.questions.length||fields.length,n=doneCount();
    progressFill.style.width=(state.done?100:state.started?Math.min(94,Math.round(n/total*100)):0)+'%';
    progressCount.textContent=state.done?'访谈完成':state.started?`${n} / ${total} 项已梳理${state.pendingClarification?' · 正在澄清':''}`:'准备开始';
    $('#session-meta').textContent=state.started?(state.done?'已完成 · 可查看需求草稿':'进行中 · 约 3 分钟'):'还没开始 · 约 3 分钟';
  }
  function renderInsights(){
    const box=$('#insight-list'),entries=[];
    if(state.initial)entries.push({label:'初步想法',value:state.initial,status:'confirmed'});
    fields.forEach(f=>{const a=state.answers[f.key];if(a)entries.push({key:f.key,label:f.label,value:a.value,status:a.status||'confirmed'});});
    state.supplements.forEach(s=>entries.push({label:'补充说明',value:s,status:'open'}));
    if(!entries.length){box.innerHTML='<div class="empty-insight"><span>◌</span><p>开始对话后<br>这里会出现需求要点</p></div>';return;}
    box.innerHTML=entries.map(e=>`<div class="insight-item"><i class="insight-status ${e.status==='open'?'open':'confirmed'}"></i><div><small>${escapeHtml(e.label)} · ${e.status==='open'?'待确认':'已记录'}</small><p>${escapeHtml(e.value)}</p>${e.key?`<button type="button" class="edit-insight" data-edit-field="${e.key}">修改</button>`:''}</div></div>`).join('');
  }
  $('#insight-list').addEventListener('click',event=>{
    const button=event.target.closest('[data-edit-field]');if(!button)return;
    const key=button.dataset.editField,field=fields.find(item=>item.key===key),current=state.answers[key]?.value||'';
    const revised=window.prompt(`修改「${field.label}」；确认后的内容会标记为已确认。`,current);
    if(revised===null)return;
    if(!revised.trim()){toast('内容不能为空；如暂不确定，请保留并标记待确认');return;}
    state.answers[key]=Agent.editedAnswer(revised);
    renderInsights();setProgress();toast('需求画像已更新，请重新核对草稿');
  });
  function promptFor(field){return Agent.getQuestion(field.key,state.domain.id);}
  function showQuestion(){
    if(state.index>=state.questions.length){finishInterview();return;}
    const field=state.pendingClarification?.field||state.questions[state.index];
    const text=state.pendingClarification?Agent.followup(field.key,state.domain.id):promptFor(field);
    setTimeout(()=>{
      const sub=state.pendingClarification?'补充澄清':`${field.label} · ${state.index+1}/${state.questions.length}`;
      addMessage(text,'assistant',sub);
      const quick=document.createElement('div');quick.className='quick-replies';
      if(!state.pendingClarification){
        field.choices.forEach(choice=>{const b=document.createElement('button');b.className='quick-reply';b.textContent=choice;b.addEventListener('click',()=>{if(choice.includes('我来描述')){input.focus();input.placeholder='补充你的具体情况…';return;}answer(choice,'choice');});quick.appendChild(b);});
      }
      const skip=document.createElement('button');skip.className='quick-reply skip-reply';skip.textContent='暂时跳过，列为待确认';skip.addEventListener('click',skipCurrentQuestion);quick.appendChild(skip);messages.appendChild(quick);
      $('#chat-area').scrollTop=$('#chat-area').scrollHeight;input.placeholder=state.pendingClarification?'补充具体例子或细节…':'输入你的回答，或选择上方选项…';
    },180);
  }
  function begin(text){
    if(state.started)return;
    state.started=true;state.initial=text.trim();state.domain=Agent.classify(text);state.questions=Agent.getOrder(state.domain.id).map(k=>fields.find(f=>f.key===k));
    welcome.style.display='none';addMessage(text,'user');$('#crumb-title').textContent=state.domain.label;
    addMessage(`我先把它归到「${state.domain.label}」场景。接下来我会优先澄清最影响需求范围的信息；如果回答比较笼统，我会再问一个具体例子。你也可以随时说“不确定”。`);
    renderInsights();setProgress();showQuestion();
  }
  function skipCurrentQuestion(){
    if(!state.started||state.done)return;
    const field=state.pendingClarification?.field||state.questions[state.index];
    const prior=state.answers[field.key]?.value;
    state.answers[field.key]=Agent.skippedAnswer(prior);
    addMessage('暂时跳过，之后可以在需求画像中修改。','user');
    state.pendingClarification=null;state.index++;
    renderInsights();setProgress();
    if(state.index<state.questions.length)showQuestion();else finishInterview();
  }
  function answer(value,source='text'){
    if(!state.started||state.done)return;
    const field=state.pendingClarification?.field||state.questions[state.index];addMessage(value,'user');
    if(state.pendingClarification){
      const previous=state.answers[field.key]?.value||'';
      state.answers[field.key]={value:`${previous}；补充说明：${value}`,status:/不确定|没想好|待确认/.test(value)?'open':'confirmed',source:'user-answer'};
      state.pendingClarification=null;state.index++;
    }else{
      const uncertain=/不确定|没想好|还没想|暂时没有标准/.test(value);
      state.answers[field.key]={value,status:uncertain?'open':'confirmed',source:'user-answer'};
      if(!state.followed[field.key]&&(uncertain||Agent.needsClarification(value,source))){
        state.followed[field.key]=true;state.pendingClarification={field};
      }else state.index++;
    }
    renderInsights();setProgress();
    if(state.index<state.questions.length)showQuestion();else if(state.pendingClarification)showQuestion();else finishInterview();
  }
  function finishInterview(){
    if(state.done)return;state.done=true;setProgress();
    addMessage('访谈已整理完成。我根据你的回答生成了需求草稿；待确认内容和 Agent 建议会单独标出。请在正式评审或开发前核对。');
    const controls=document.createElement('div');controls.className='quick-replies';controls.innerHTML='<button class="quick-reply" id="open-doc-inline">查看需求草稿 ↗</button><button class="quick-reply" id="restart-inline">重新开始</button>';
    messages.appendChild(controls);$('#open-doc-inline').addEventListener('click',openDoc);$('#restart-inline').addEventListener('click',reset);$('#chat-area').scrollTop=$('#chat-area').scrollHeight;input.placeholder='补充其他信息…';
  }
  function addSupplement(text){
    const key=Agent.mapSupplement(text);
    if(key&&state.answers[key]){
      const current=state.answers[key].value;
      state.answers[key]={value:`${current}；补充（待确认）：${text}`,status:'open',source:'user-supplement'};
      addMessage(`这条补充看起来与「${fields.find(f=>f.key===key).label}」有关。我已附加到该项并标为待确认，请在需求草稿中核对。`);
    }else{
      state.supplements.push(text);addMessage('我已把这条内容列为“补充说明（待确认）”。它还没有自动合并到具体需求字段，请在草稿中核对。');
    }
    renderInsights();toast('补充内容已记录，草稿已更新');
  }
  function submit(){const val=input.value.trim();if(!val)return;input.value='';input.style.height='auto';if(!state.started){begin(val);return;}if(state.done){addMessage(val,'user');addSupplement(val);return;}answer(val,'text');}
  send.addEventListener('click',submit);input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit();}});input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,100)+'px';});
  function reset(){state.started=false;state.initial='';state.domain=null;state.index=0;state.answers={};state.questions=[];state.done=false;state.pendingClarification=null;state.followed={};state.supplements=[];messages.innerHTML='';welcome.style.display='block';input.value='';input.placeholder='先说说你想解决什么问题…';$('#crumb-title').textContent='新建需求访谈';setProgress();renderInsights();$('#doc-modal').classList.remove('open');}
  $('#nav-new').addEventListener('click',reset);$('#nav-doc').addEventListener('click',()=>state.started?openDoc():toast('先开始一场需求访谈吧'));
  function val(key,fallback='待确认'){return state.answers[key]?.value||fallback;}
  function marked(key){const a=state.answers[key];return a?.status==='open'?'（待确认）':'';}
  function docMarkdown(){
    const title=`${state.domain?.title||'需求方案'}（草稿）`;
    const uncertain=fields.filter(f=>!state.answers[f.key]||state.answers[f.key].status==='open');
    const details=state.supplements.length?state.supplements.map(x=>`- ${x}（待确认，尚未归入具体需求字段）`).join('\n'):'- 无额外补充。';
    const provenance=fields.map(f=>{const a=state.answers[f.key];const source=Agent.provenanceLabel(a);return `- **${f.label}：** ${source}${a?.status==='open'?'；待确认':''}`;}).join('\n');
    return `# ${title}\n\n> 草稿由需求翻译官根据本次访谈整理；请需求提出者核对后再用于评审或开发。\n\n## 1. 需求摘要\n${state.initial||'待补充'}\n\n## 2. 目标用户与场景\n- **目标用户：** ${val('users')}${marked('users')}\n- **关键流程：** ${val('flow')}${marked('flow')}\n\n## 3. 当前痛点与预期结果\n- **核心痛点：** ${val('pain')}${marked('pain')}\n- **预期结果：** ${val('outcome')}${marked('outcome')}\n\n## 4. 功能需求（初稿）\n- 围绕上述用户与场景，支持完成：${val('flow')}${marked('flow')}。\n- 功能边界及实现细节需由需求方与产品/研发进一步确认；未覆盖内容不视为已确定需求。\n\n## 5. 范围与约束\n${val('scope')}${marked('scope')}\n\n## 6. 验收标准（草稿）\n- **用户提供的判断标准：** ${val('acceptance')}${marked('acceptance')}。\n- **Agent 写法建议：** 可将目标进一步改写为可测量条件，例如“在指定场景下，用户可在 X 分钟内完成 Y”。该示例不是已确认指标。\n\n## 7. 待确认事项\n${uncertain.length?uncertain.map(f=>`- **${f.label}：** ${state.answers[f.key]?.value||'尚未收集，请补充确认。'}`).join('\n'):'- 本轮问题均已作答；仍建议审核功能边界和验收标准。'}\n\n## 8. 额外补充\n${details}\n\n## 9. 信息来源追溯\n- **初始想法：** 用户输入。\n${provenance}\n- 补充说明由用户输入；未自动归类的内容单列为待确认。\n\n## 10. 信息状态与能力边界\n- 本草稿依据本次用户输入整理；待确认项明确标记，跳过问题不会伪装成已回答。\n- 当前原型采用本地规则进行场景分类、问题排序和笼统回答追问，不调用大语言模型。\n- Agent 建议不代表用户承诺；本工具不替代业务、产品、技术和合规评审。\n`;
  }
  function openDoc(){if(!state.started){toast('先开始一场需求访谈吧');return;}$('#doc-body').innerHTML=markdownToHtml(docMarkdown());$('#doc-date').textContent=new Date().toLocaleDateString('zh-CN');$('#doc-modal').classList.add('open');$('#doc-modal').setAttribute('aria-hidden','false');}
  function markdownToHtml(md){return md.split('\n').map(line=>{if(line.startsWith('# '))return `<h3>${escapeHtml(line.slice(2))}</h3>`;if(line.startsWith('## '))return `<h3>${escapeHtml(line.slice(3))}</h3>`;if(line.startsWith('> '))return `<div class="doc-note">${escapeHtml(line.slice(2))}</div>`;if(line.startsWith('- '))return `<p>• ${escapeHtml(line.slice(2)).replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')}</p>`;return line?`<p>${escapeHtml(line)}</p>`:'';}).join('');}
  $('#close-modal').addEventListener('click',()=>$('#doc-modal').classList.remove('open'));$('#doc-modal').addEventListener('click',e=>{if(e.target.id==='doc-modal')$('#doc-modal').classList.remove('open');});
  $('#copy-doc').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(docMarkdown());toast('需求文档已复制')}catch{toast('复制失败，请手动选择文档内容')}});
  $('#download-doc').addEventListener('click',()=>{const blob=new Blob(['\ufeff'+docMarkdown()],{type:'text/markdown;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='需求翻译官-需求草稿.md';a.click();URL.revokeObjectURL(a.href);toast('Markdown 文档已下载');});
  let toastTimer;function toast(text){const t=$('#toast');t.textContent=text;t.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('show'),2400);}
  document.addEventListener('keydown',e=>{if(e.key==='Escape')$('#doc-modal').classList.remove('open');if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();reset();input.focus();}});
  setProgress();renderInsights();
})();
