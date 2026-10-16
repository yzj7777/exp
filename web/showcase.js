(() => {
  const examples={
    meeting:{domain:'会议协作场景',user:'我想让团队会议协作更高效。',question:'在会议前、会议中或会后，哪个环节最让团队耗时或容易遗漏？',confirmed:'待用户确认 · 具体痛点'},
    order:{domain:'订单查询场景',user:'希望客户能自己查到订单进度。',question:'客户现在查询订单时最常遇到什么问题？找不到进度、信息不及时，还是需要联系人工？',confirmed:'待用户确认 · 查询中的阻碍'},
    coding:{domain:'研发工具场景',user:'想做个工具让代码审查轻松一点。',question:'当前代码审查中最耗时或最容易遗漏的具体问题是什么？',confirmed:'待用户确认 · 审查痛点'}
  };
  document.querySelectorAll('.sample-tab').forEach(button=>button.addEventListener('click',()=>{
    const data=examples[button.dataset.demo];if(!data)return;
    document.querySelectorAll('.sample-tab').forEach(tab=>tab.classList.toggle('active',tab===button));
    document.querySelector('#sample-domain').textContent=data.domain;
    document.querySelector('#sample-user').textContent=data.user;
    document.querySelector('#sample-question').textContent=data.question;
    document.querySelector('#sample-confirmed').textContent=data.confirmed;
  }));
})();
