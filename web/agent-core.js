/* Deterministic, local-only interview policy for the prototype. This is not an LLM. */
(function (root) {
  const domains = [
    {id:'meeting',label:'会议协作',title:'会议管理功能需求',re:/会议|纪要|会后|参会|议程|会议室/},
    {id:'order',label:'订单查询',title:'订单进度查询需求',re:/订单|物流|配送|发货|售后|快递/},
    {id:'coding',label:'研发工具',title:'研发工具需求',re:/代码|开发|编程|测试|bug|缺陷|接口|仓库/},
    {id:'research',label:'科研工作',title:'科研工作流需求',re:/科研|文献|实验|论文|数据分析|研究/}
  ];
  const orderByDomain={
    meeting:['pain','users','flow','outcome','scope','acceptance'],
    order:['users','flow','pain','outcome','scope','acceptance'],
    coding:['users','pain','flow','scope','outcome','acceptance'],
    research:['users','pain','outcome','flow','scope','acceptance'],
    general:['users','pain','outcome','flow','scope','acceptance']
  };
  const questions={
    users:{generic:'谁会最常使用这个功能？可以说一个具体角色或典型用户。',meeting:'这个会议流程里，谁最需要使用它？例如组织者、参会者还是团队负责人？',order:'谁会查询订单进度？是下单客户、客服，还是其他角色？',coding:'主要使用者是谁？例如个人开发者、研发团队还是代码审查者？',research:'主要使用者是谁？例如研究人员、学生还是实验室团队？'},
    pain:{generic:'他们现在遇到的最具体、最麻烦的问题是什么？发生在什么环节？',meeting:'在会议前、会议中或会后，哪个环节最让团队耗时或容易遗漏？',order:'客户现在查询订单时最常遇到什么问题？例如找不到进度、信息更新不及时，还是需要反复联系人工客服？',coding:'当前研发流程中最耗时或最容易出错的环节是什么？',research:'在文献、实验或数据分析流程中，最需要改善的具体环节是什么？'},
    outcome:{generic:'如果这个需求做好了，你最希望看到什么变化？',meeting:'这个功能上线后，你希望会议协作具体有什么变化？',order:'客户使用后，最希望能独立完成什么事情？',coding:'你希望研发人员完成什么任务时更快、更可靠？',research:'你希望研究人员在哪项工作上获得可观察的改善？'},
    flow:{generic:'设想一次典型使用：用户从什么动作开始，最后希望完成什么？',meeting:'以一次会议为例，用户从哪个动作开始，直到会后希望完成什么？',order:'客户会从哪里进入查询？查询后需要看到哪些关键进度或后续操作？',coding:'以一个典型任务为例，输入是什么，工具需要协助完成什么，结果交付到哪里？',research:'以一次典型研究任务为例，用户提供什么材料，最后希望拿到什么结果？'},
    scope:{generic:'有没有必须遵守的限制或暂时不做的部分？例如权限、设备、系统对接或上线范围。',meeting:'这个功能需要和日历、会议软件或任务工具对接吗？有哪些权限或范围限制？',order:'订单信息来自哪个现有系统？查询时有哪些身份验证或数据权限要求？',coding:'需要支持哪些代码仓库、语言或开发工具？有哪些安全或权限限制？',research:'需要连接哪些数据源或科研工具？数据授权、隐私或使用范围有哪些限制？'},
    acceptance:{generic:'你会用什么现象判断它真的解决了问题？尽量说一个可以观察或衡量的标准。',meeting:'你会用什么可观察的指标判断会议协作改善了？例如会后任务遗漏率或整理纪要耗时。',order:'怎样判断查询体验达标？例如客户能否独立找到状态、信息是否及时准确。',coding:'怎样验证工具确实有帮助？例如任务完成时间、缺陷发现率或测试覆盖情况。',research:'用什么可观察结果判断工具有帮助？例如文献整理时间或数据分析步骤的可复现性。'}
  };
  const fuzzy=/不知道|不确定|没想好|还没想|更方便|提高效率|更快|更好|智能|好用|其他|差不多|尽量|简单一点|暂时没有标准/;
  function classify(text=''){return domains.find(d=>d.re.test(text))||{id:'general',label:'通用需求',title:'需求方案'};}
  function getOrder(domain='general'){return (orderByDomain[domain]||orderByDomain.general).slice();}
  function getQuestion(field,domain='general'){return questions[field]?.[domain]||questions[field]?.generic||'可以再具体说明一下吗？';}
  function needsClarification(value,source='text'){
    if(source==='choice') return false;
    const v=(value||'').trim();
    return v.length<8||fuzzy.test(v);
  }
  function followup(field,domain='general'){
    const byField={
      users:'你提到的用户还比较宽泛。能否说一个最典型的具体角色，以及他在什么情况下使用？',
      pain:'能举一个最近发生的具体例子吗？当时用户做了什么，卡在哪里？',
      outcome:'“更好/更快”还不够容易验证。你最希望减少哪种时间、错误或操作？',
      flow:'能把开始动作和最终结果各说清楚一点吗？中间最关键的一步是什么？',
      scope:'哪些内容明确不在本次范围内？如果暂时没有，也可以明确说“暂无已知限制”。',
      acceptance:'请尽量给一个可以观察的判断方法；暂时没有指标时，可以说最重要的体验变化。'
    };
    if(field==='pain'&&domain==='meeting')return '你提到会议协作。能回忆一个最近的具体例子吗？哪个环节发生了什么问题？';
    if(field==='flow'&&domain==='order')return '请具体说说客户从哪里开始查询、最终需要看到哪些信息？';
    return byField[field]||'能提供一个具体例子吗？';
  }
  function mapSupplement(text=''){
    const rules=[['scope',/权限|范围|限制|系统|对接|数据/],['acceptance',/验收|指标|标准|成功|衡量|分钟|比例|率/],['pain',/问题|痛点|麻烦|耗时|遗漏|错误|困难/],['outcome',/目标|希望|提升|减少|节省|结果/],['flow',/流程|步骤|开始|之后|最后|操作/],['users',/用户|客户|员工|管理员|角色|谁用/]];
    return rules.find(([,re])=>re.test(text))?.[0]||null;
  }
  function skippedAnswer(previous=''){
    return {value:previous?`${previous}；用户暂时跳过补充澄清`:'用户暂时跳过，尚未提供',status:'open',source:'skip'};
  }
  function editedAnswer(value=''){
    const text=(value||'').trim();
    return {value:text,status:/不确定|没想好|待确认|尚未/.test(text)?'open':'confirmed',source:'user-edit'};
  }
  function provenanceLabel(answer){
    if(!answer)return '尚未收集';
    if(answer.source==='user-edit')return '用户修改确认';
    if(answer.source==='skip')return '用户跳过（待确认）';
    if(answer.source==='user-supplement')return '用户补充';
    return '用户访谈回答';
  }
  root.RequirementAgent={classify,getOrder,getQuestion,needsClarification,followup,mapSupplement,skippedAnswer,editedAnswer,provenanceLabel};
  if(typeof module!=='undefined'&&module.exports) module.exports=root.RequirementAgent;
})(typeof window!=='undefined'?window:globalThis);
