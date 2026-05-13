import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = path.resolve("outputs");
const outputPath = path.join(outputDir, "meta_report_last_2_weeks.xlsx");

const report = {
  period: { start: "2026-04-22", end: "2026-05-05" },
  account: { id: "act_1746501262698286", sourceNote: "Meta API; repeat refresh hit API rate limit, workbook uses the latest successful pull in this thread." },
  summary: [
    ["Spend", 4192.38],
    ["Impressions", 607846],
    ["Clicks", 3686],
    ["CTR", 0.006064],
    ["CPC", 1.14],
    ["CPM", 6.9],
  ],
  campaigns: [
    ["120237744982200308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_leadgeneration_december_video", "OUTCOME_LEADS", 2423.98, 338917, 198832, 1484, 0, 0.004379, 1.63, 7.15, 0],
    ["120234421810920308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_traffic", "LINK_CLICKS", 1348.99, 214847, 131495, 1740, 0, 0.008099, 0.78, 6.28, 0],
    ["120243628303150308", "hm_varikozanet_almaty_invalve_whatsapp", "OUTCOME_ENGAGEMENT", 369.0, 50853, 31084, 441, 0, 0.008672, 0.84, 7.26, 0],
    ["120237747381540308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_traffic_retarget_lal", "LINK_CLICKS", 50.41, 3229, 2384, 21, 0, 0.006504, 2.4, 15.61, 0],
  ],
  adsets: [
    ["120234423272280308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_traffic_kreo2", "LINK_CLICKS", 1349.0, 214848, 131495, 1740, 0, 0.008099, 0.78, 6.28, 0],
    ["120237744982220308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_leadgeneration_december_video_1", "OUTCOME_LEADS", 1167.11, 166872, 122838, 643, 0, 0.003853, 1.82, 6.99, 0],
    ["120241852550810308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_leadgeneration_march_video_1", "OUTCOME_LEADS", 748.92, 89600, 50302, 366, 0, 0.004085, 2.05, 8.36, 0],
    ["120237745682770308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_leadgeneration_december_video_3", "OUTCOME_LEADS", 257.51, 38906, 28898, 275, 0, 0.007068, 0.94, 6.62, 0],
    ["120237948452100308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_leadgeneration_december_video_5", "OUTCOME_LEADS", 250.44, 43539, 30644, 200, 0, 0.004594, 1.25, 5.75, 0],
    ["120243628303160308", "hm_varikozanet_almaty_invalve_whatsapp_interesy_statika", "OUTCOME_ENGAGEMENT", 227.32, 28732, 18720, 284, 0, 0.009884, 0.8, 7.91, 0],
    ["120243840734720308", "hm_varikozanet_almaty_invalve_whatsapp_interesy_video", "OUTCOME_ENGAGEMENT", 141.68, 22121, 14100, 157, 0, 0.007097, 0.9, 6.4, 0],
    ["120237752813380308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_traffic_lal_otpravili_formu", "LINK_CLICKS", 50.41, 3229, 2384, 21, 0, 0.006504, 2.4, 15.61, 0],
  ],
  ads: [
    ["120234423272290308", "traffic_kreo2", "LINK_CLICKS", 1348.99, 214847, 131495, 1740, 0, 0.008099, 0.78, 6.28, 0],
    ["120237744982210308", "leadgeneration_december_video_1", "OUTCOME_LEADS", 1167.11, 166872, 122838, 643, 0, 0.003853, 1.82, 6.99, 0],
    ["120241852550800308", "leadgeneration_march_video_1", "OUTCOME_LEADS", 748.92, 89600, 50302, 366, 0, 0.004085, 2.05, 8.36, 0],
    ["120237745682780308", "leadgeneration_december_video_3", "OUTCOME_LEADS", 257.51, 38906, 28898, 275, 0, 0.007068, 0.94, 6.62, 0],
    ["120237948452150308", "leadgeneration_december_video_5", "OUTCOME_LEADS", 250.44, 43539, 30644, 200, 0, 0.004594, 1.25, 5.75, 0],
    ["120243655250910308", "invalve_whatsapp_interesy_banner_2", "OUTCOME_ENGAGEMENT", 151.72, 19086, 14172, 200, 0, 0.010479, 0.76, 7.95, 0],
    ["120243840734710308", "invalve_whatsapp_interesy_video_Узи вен + диагностика", "OUTCOME_ENGAGEMENT", 141.68, 22121, 14100, 157, 0, 0.007097, 0.9, 6.4, 0],
    ["120243628303170308", "invalve_whatsapp_interesy_banner_1", "OUTCOME_ENGAGEMENT", 68.75, 8357, 5851, 74, 0, 0.008855, 0.93, 8.23, 0],
    ["120237752813390308", "traffic_lal_otpravili_formu_1", "LINK_CLICKS", 46.75, 2970, 2262, 19, 0, 0.006397, 2.46, 15.74, 0],
    ["120237752813400308", "traffic_lal_otpravili_formu_4", "LINK_CLICKS", 1.69, 117, 106, 1, 0, 0.008547, 1.69, 14.44, 0],
  ],
  issues: [
    ["campaign", "120244590515780308", "Тест", "PAUSED", ""],
    ["campaign", "120243628303150308", "hm_varikozanet_almaty_invalve_whatsapp", "PAUSED", ""],
    ["campaign", "120241227136750308", "hm_varikozanet_almaty_whatsapp_invalve_0024_до_15.03", "PAUSED", ""],
    ["campaign", "120240521073890308", "hm_varikozanet_almaty_invalve_whatsapp_14feb", "PAUSED", ""],
    ["campaign", "120239396184330308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_traffic_akciya_kaspi", "PAUSED", ""],
    ["campaign", "120237747381540308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_traffic_retarget_lal", "PAUSED", ""],
    ["campaign", "120236966445030308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis_traffic_december", "PAUSED", ""],
    ["campaign", "120234421336680308", "hm_varikozanet_almaty_call_lechenie_varikoza_zapis", "PAUSED", ""],
    ["campaign", "120234246142810308", "hm_varikozanet_almaty_whatsapp_lechenie_varikoza_zapis", "PAUSED", ""],
    ["campaign", "120233676700880308", "hm_varikozanet_almaty_leadform_lechenie_varikoza_zapis_test", "PAUSED", ""],
  ],
};

const metricHeaders = ["ID", "Name", "Objective", "Spend", "Impressions", "Reach", "Clicks", "Conversions", "CTR", "CPC", "CPM", "Cost / result"];

function money(range) {
  range.format.numberFormat = "#,##0.00";
}

function percent(range) {
  range.format.numberFormat = "0.00%";
}

function styleTable(sheet, rangeAddress, tableName) {
  const table = sheet.tables.add(rangeAddress, true, tableName);
  table.style = "TableStyleMedium2";
  table.showFilterButton = true;
  sheet.freezePanes.freezeRows(1);
  sheet.getRange(rangeAddress).format.wrapText = false;
  return table;
}

function setupMetricSheet(workbook, name, rows, tableName) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  const data = [metricHeaders, ...rows];
  sheet.getRangeByIndexes(0, 0, data.length, metricHeaders.length).values = data;
  styleTable(sheet, `A1:L${data.length}`, tableName);
  sheet.getRange("A:A").format.columnWidthPx = 145;
  sheet.getRange("B:B").format.columnWidthPx = 430;
  sheet.getRange("C:C").format.columnWidthPx = 150;
  sheet.getRange("D:L").format.columnWidthPx = 105;
  money(sheet.getRange(`D2:D${data.length}`));
  sheet.getRange(`E2:H${data.length}`).format.numberFormat = "#,##0";
  percent(sheet.getRange(`I2:I${data.length}`));
  money(sheet.getRange(`J2:L${data.length}`));
  return sheet;
}

await fs.mkdir(outputDir, { recursive: true });

const workbook = Workbook.create();

const summary = workbook.worksheets.add("Summary");
summary.showGridLines = false;
summary.getRange("A1:F1").merge();
summary.getRange("A1").values = [["Meta Ads report: last two weeks"]];
summary.getRange("A1").format = { font: { bold: true, size: 18, color: "#12312B" } };
summary.getRange("A2:F2").merge();
summary.getRange("A2").values = [[`Period: ${report.period.start} to ${report.period.end} | Account: ${report.account.id}`]];
summary.getRange("A4:B9").values = [["Metric", "Value"], ...report.summary];
styleTable(summary, "A4:B10", "SummaryTable");
money(summary.getRange("B5:B5"));
summary.getRange("B6:B7").format.numberFormat = "#,##0";
percent(summary.getRange("B8:B8"));
money(summary.getRange("B9:B10"));
summary.getRange("D4:H4").values = [["Main finding", "Evidence", "Recommended action", "Priority", "Owner"]];
summary.getRange("D5:H8").values = [
  ["Conversions are zero in API", "All reported campaign/ad rows show 0 conversions", "Check Meta result event, Pixel/custom conversion, WhatsApp attribution and API action type", "High", "Media buyer"],
  ["Lead campaigns spend heavily with weak CTR", "Top lead campaign spent 2,423.98 with 0.44% CTR and 1.63 CPC", "Refresh hooks and shift budget from low-CTR adsets until conversion tracking is fixed", "High", "Creative + buyer"],
  ["Traffic campaign has cheaper clicks", "Traffic campaign CPC 0.78 vs lead adsets up to 2.05", "Use it as traffic baseline, but judge scaling only by real WhatsApp/lead cost", "Medium", "Media buyer"],
  ["Retarget/LAL is expensive at low volume", "Retarget/LAL CPC 2.40 and CPM 15.61", "Keep capped until audience quality and tracking are validated", "Medium", "Media buyer"],
];
styleTable(summary, "D4:H8", "FindingsTable");
summary.getRange("A:A").format.columnWidthPx = 150;
summary.getRange("B:B").format.columnWidthPx = 150;
summary.getRange("D:D").format.columnWidthPx = 230;
summary.getRange("E:E").format.columnWidthPx = 260;
summary.getRange("F:F").format.columnWidthPx = 360;
summary.getRange("G:H").format.columnWidthPx = 100;
summary.getRange("D5:F8").format.wrapText = true;

summary.getRange("A12:B16").values = [["Campaign", "Spend"], ...report.campaigns.map((row) => [String(row[1]).slice(0, 32), row[3]])];
money(summary.getRange("B13:B16"));
const chart = summary.charts.add("bar", summary.getRange("A12:B16"));
chart.title = "Spend by campaign";
chart.hasLegend = false;
chart.xAxis = { axisType: "textAxis" };
chart.yAxis = { numberFormatCode: "#,##0" };
chart.setPosition("D10", "H25");

setupMetricSheet(workbook, "Campaigns", report.campaigns, "CampaignsTable");
setupMetricSheet(workbook, "Adsets", report.adsets, "AdsetsTable");
setupMetricSheet(workbook, "Ads", report.ads, "AdsTable");
setupMetricSheet(workbook, "No result ads", report.ads.filter((row) => row[7] === 0 && row[3] >= 20), "NoResultAdsTable");

const issues = workbook.worksheets.add("Issues");
issues.showGridLines = false;
const issueHeaders = ["Object type", "ID", "Name", "Status", "Policy / review note"];
issues.getRangeByIndexes(0, 0, report.issues.length + 1, issueHeaders.length).values = [issueHeaders, ...report.issues];
styleTable(issues, `A1:E${report.issues.length + 1}`, "IssuesTable");
issues.getRange("A:B").format.columnWidthPx = 150;
issues.getRange("C:C").format.columnWidthPx = 430;
issues.getRange("D:E").format.columnWidthPx = 160;

const notes = workbook.worksheets.add("Notes");
notes.showGridLines = false;
notes.getRange("A1:B6").values = [
  ["Item", "Note"],
  ["Period", `${report.period.start} to ${report.period.end}`],
  ["Source", report.account.sourceNote],
  ["Rate limit", "A repeated refresh after the successful pull returned Meta API rate limit errors; avoid immediate repeated API pulls."],
  ["Conversion caveat", "Conversions are zero as returned by the configured API action metrics. Validate Ads Manager result columns before making budget decisions."],
  ["Burnout", "No burnout signals were returned in the successful pull."],
];
styleTable(notes, "A1:B6", "NotesTable");
notes.getRange("A:A").format.columnWidthPx = 170;
notes.getRange("B:B").format.columnWidthPx = 650;
notes.getRange("B:B").format.wrapText = true;

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "formula error scan",
});
console.log(errors.ndjson);

await workbook.render({ sheetName: "Summary", autoCrop: "all", scale: 1, format: "png" });
await workbook.render({ sheetName: "Campaigns", autoCrop: "all", scale: 1, format: "png" });
await workbook.render({ sheetName: "Ads", autoCrop: "all", scale: 1, format: "png" });

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
