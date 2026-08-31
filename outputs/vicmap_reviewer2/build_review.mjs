import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const inputPath = 'D:/xwechat_files/wxid_fynu0rcjs47f21_b973/msg/file/2026-08/vicmap_qa_sample(1).csv';
const outputPath = 'E:/Github/active-together/outputs/vicmap_reviewer2/vicmap_qa_reviewer2_checked.xlsx';
const previewDir = 'E:/Github/active-together/outputs/vicmap_reviewer2/previews';
const csvText = await fs.readFile(inputPath, 'utf8');
const workbook = await Workbook.fromCSV(csvText, { sheetName: 'QA' });
const qa = workbook.worksheets.getItem('QA');
const used = qa.getUsedRange();
const values = used.values;
const rowCount = values.length - 1;

const notesByCategory = {
  park_and_garden: 'Name indicates a park, reserve, garden or landscaped open space; category matches.',
  sports_ground: 'Name indicates a sports field, ground, complex or sports venue; category matches.',
  playground: 'Name identifies a playground; category matches.',
  court: 'Name identifies a sports court or court-based venue; category matches.',
  picnic_day_use: 'Name identifies a picnic or day-use area; category matches.',
  skate_bmx: 'Name identifies a skate, BMX, velodrome or extreme-sports facility; category matches.',
  trail_access: 'Name identifies a trail entrance or access point; category matches.'
};

const reviewerRows = [];
for (let i = 1; i < values.length; i++) {
  const sampleId = String(values[i][0]);
  const category = String(values[i][4]);
  if (sampleId === '61') {
    reviewerRows.push(['incorrect', 'park_and_garden', 'Name “Sculpture Lawn” indicates a landscaped lawn/open space, not a picnic or day-use area.']);
  } else {
    reviewerRows.push(['included', '', notesByCategory[category] ?? 'Name is consistent with the assigned activity category.']);
  }
}
qa.getRange(`O2:Q${rowCount + 1}`).values = reviewerRows;

qa.freezePanes.freezeRows(1);
qa.getRange('A1:T1').format = { fill: '#1F4E78', font: { bold: true, color: '#FFFFFF' }, wrapText: true };
qa.getRange('A1:T1').format.rowHeight = 34;
qa.getRange('A2:T153').format.font = { name: 'Aptos', size: 10 };
qa.getRange('C:C').format.columnWidth = 36;
qa.getRange('E:E').format.columnWidth = 20;
qa.getRange('O:P').format.columnWidth = 20;
qa.getRange('Q:Q').format.columnWidth = 58;
qa.getRange('Q2:Q153').format.wrapText = true;

const summary = workbook.worksheets.add('Summary');
summary.getRange('A1:B5').values = [
  ['Reviewer 2 name/category QA', 'Value'],
  ['Included', null],
  ['Incorrect', null],
  ['Total', null],
  ['Accuracy', null]
];
summary.getRange('B2').formulas = [[`=COUNTIF('QA'!$O$2:$O$${rowCount + 1},"included")`]];
summary.getRange('B3').formulas = [[`=COUNTIF('QA'!$O$2:$O$${rowCount + 1},"incorrect")`]];
summary.getRange('B4').formulas = [['=B2+B3']];
summary.getRange('B5').formulas = [['=B2/B4']];
summary.getRange('B5').format.numberFormat = '0.00%';
summary.getRange('A1:B1').format = { fill: '#1F4E78', font: { bold: true, color: '#FFFFFF' } };
summary.getRange('A2:A5').format.font = { bold: true };
summary.getRange('A1:B5').format.borders = { preset: 'outside', style: 'thin', color: '#B4C6E7' };
summary.getRange('A:A').format.columnWidth = 30;
summary.getRange('B:B').format.columnWidth = 16;
summary.showGridLines = false;

await fs.mkdir(previewDir, { recursive: true });
const summaryPreview = await workbook.render({ sheetName: 'Summary', range: 'A1:B5', scale: 2, format: 'png' });
await fs.writeFile(`${previewDir}/summary.png`, new Uint8Array(await summaryPreview.arrayBuffer()));
const qaPreview = await workbook.render({ sheetName: 'QA', range: 'A1:Q15', scale: 1, format: 'png' });
await fs.writeFile(`${previewDir}/qa.png`, new Uint8Array(await qaPreview.arrayBuffer()));

const check = await workbook.inspect({ kind: 'table', range: 'Summary!A1:B5', include: 'values,formulas', tableMaxRows: 8, tableMaxCols: 4 });
console.log(check.ndjson);
const errors = await workbook.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A', options: { useRegex: true, maxResults: 50 }, summary: 'final formula error scan' });
console.log(errors.ndjson);
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
