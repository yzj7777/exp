const fs = require('node:fs');
const path = require('node:path');
const Agent = require('../web/agent-core.js');
const cases = JSON.parse(fs.readFileSync(path.join(__dirname, 'evaluation-cases.json'), 'utf8'));
const matrix = {};
let correct = 0;
for (const item of cases) {
  const predicted = Agent.classify(item.text).id;
  const row = matrix[item.expected] ||= { total: 0, correct: 0 };
  row.total++;
  if (predicted === item.expected) { row.correct++; correct++; }
  else console.log(`MISCLASSIFIED expected=${item.expected} predicted=${predicted}: ${item.text}`);
}
const vagueCases = [
  {text:'提高效率', expected:true},
  {text:'更方便一点', expected:true},
  {text:'还没想好', expected:true},
  {text:'我不知道具体要什么', expected:true},
  {text:'通过会后任务提醒减少负责人遗漏', expected:false},
  {text:'客户在订单详情页查看实时物流节点', expected:false},
  {text:'管理员审核员工提交的申请并记录处理结果', expected:false},
  {text:'暂时没有标准，帮我建议', expected:true}
];
let vagueCorrect=0;
for(const item of vagueCases){
  const actual=Agent.needsClarification(item.text,'text');
  if(actual===item.expected)vagueCorrect++;
  else console.log(`CLARIFICATION MISMATCH expected=${item.expected} actual=${actual}: ${item.text}`);
}
const accuracy=correct/cases.length, vagueAccuracy=vagueCorrect/vagueCases.length;
console.log(`Scenario classification: ${correct}/${cases.length} (${(accuracy*100).toFixed(1)}%)`);
for(const [label,row] of Object.entries(matrix)) console.log(`  ${label}: ${row.correct}/${row.total} (${(100*row.correct/row.total).toFixed(1)}%)`);
console.log(`Vague-answer trigger checks: ${vagueCorrect}/${vagueCases.length} (${(vagueAccuracy*100).toFixed(1)}%)`);
console.log('NOTE: Small hand-authored rule checks, not user study, not a measure of requirement quality or real-world accuracy.');
if(accuracy<0.9||vagueAccuracy<0.85)process.exitCode=1;
