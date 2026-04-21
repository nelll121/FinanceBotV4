// ═══════════════════════════════════════════════════════════════════
// FinanceBot — Apps Script (минимальная версия)
// Только для ручного редактирования таблицы.
// Вся API логика перенесена в Python бот (gspread).
// ═══════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════════
// ЛИЧНЫЕ ФИНАНСЫ — Google Apps Script v4
// Исправлено: точные координаты колонок, долги в месяцах, баланс, частичный долг
// ═══════════════════════════════════════════════════════════════════════════════

// ── КОНСТАНТЫ ЖУРНАЛА ─────────────────────────────────────────────────────────
const JOURNAL_SHEET  = "📋 Журнал долгов";
const SUMMARY_SHEET  = "📊 Итоги года";
const MONTHS = ["Январь","Февраль","Март","Апрель","Май","Июнь",
                "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"];

// Колонки журнала (1-based, из диагностики: B=2...J=10)
const J_NUM    = 2;   // B — №
const J_TYPE   = 3;   // C — Тип
const J_NAME   = 4;   // D — Имя
const J_DESC   = 5;   // E — Описание
const J_AMOUNT = 6;   // F — Сумма
const J_REC    = 7;   // G — Дата записи
const J_RET    = 8;   // H — Дата возврата
const J_STATUS = 9;   // I — Статус
const J_NOTE   = 10;  // J — Примечание
const J_HEADER = 5;   // Строка с заголовками
const J_START  = 6;   // Первая строка данных
const J_END    = 55;  // Последняя строка данных

// ── ТОЧНЫЕ КООРДИНАТЫ МЕСЯЧНОГО ЛИСТА (из диагностики) ───────────────────────
// Доходы
const INC_HEADER_ROW  = 4;   // Строка заголовка блока
const INC_SUBHDR_ROW  = 5;   // Строка подзаголовков (Категория / План / Факт)
const INC_DATA_START  = 6;   // Первая строка данных
const INC_TOTAL_ROW   = 13;  // Строка "Итого" доходов
const INC_CAT_COL     = 14;  // N — Категория
const INC_PLAN_COL    = 15;  // O — Плановый
const INC_FACT_COL    = 16;  // P — Фактический

// Расходы
const EXP_HEADER_ROW  = 4;
const EXP_DATA_START  = 6;   // после подзаголовка строка 6 (аналогично)
const EXP_TOTAL_ROW   = 22;  // Строка "Итого" расходов
const EXP_CAT_COL     = 18;  // R — Категория
const EXP_PLAN_COL    = 19;  // S — Плановый
const EXP_FACT_COL    = 20;  // T — Фактический

// Долги (из диагностики)
const DME_HEADER_ROW  = 5;   // "👤 МНЕ ДОЛЖНЫ"
const DME_DATA_START  = 7;   // Данные с строки 7
const DME_DATA_END    = 14;  // До строки 14 (итого на 15)
const DME_TOTAL_ROW   = 15;  // "Итого мне должны"

const DI_HEADER_ROW   = 17;  // "👤 Я ДОЛЖЕН"
const DI_DATA_START   = 19;  // Данные с строки 19
const DI_DATA_END     = 26;  // До строки 26 (итого на 27)
const DI_TOTAL_ROW    = 27;  // "Итого я должен"

const DEBT_NAME_COL   = 26;  // Z — Имя
const DEBT_AMT_COL    = 27;  // AA — Сумма
const DEBT_DATE_COL   = 28;  // AB — Дата возврата

// Ежедневные операции (из диагностики)
const EXP_DAILY_HEADER = 31; // Строка заголовка секции
const EXP_DAILY_START  = 34; // Первые данные (header+2+subheader+1)
const EXP_DAILY_END    = 94; // Строка перед ИТОГО (95-1)
const EXP_DAILY_TOTAL  = 95;

const EXP_DATE_COL  = 2;    // B
const EXP_DESC_COL  = 3;    // C
const EXP_CAT_COL2  = 8;    // H
const EXP_AMT_COL   = 11;   // K
const EXP_NOTE_COL  = 12;   // L

const INC_DAILY_HEADER = 31; // Та же строка (слева расходы, справа поступления)
const INC_DAILY_START  = 34;
const INC_DAILY_END    = 94;
const INC_DAILY_TOTAL  = 95;

const INC_DATE_COL  = 14;   // N
const INC_DESC_COL  = 15;   // O
const INC_CAT_COL2  = 20;   // T
const INC_AMT_COL   = 23;   // W
const INC_NOTE_COL  = 24;   // X

// ═══════════════════════════════════════════════════════════════════════════════
// МЕНЮ
// ═══════════════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════════
// ON EDIT
// ═══════════════════════════════════════════════════════════════════════════════
function onEdit(e) {
  if (!e) return;
  const sheet = e.range.getSheet();
  const name  = sheet.getName();
  const row   = e.range.getRow();
  const col   = e.range.getColumn();
  const val   = String(e.value || "");
  const old   = String(e.oldValue || "");

  // Автодата в ежедневных операциях
  if (MONTHS.includes(name)) {
    if (col === EXP_AMT_COL && Number(val) > 0 &&
        row >= EXP_DAILY_START && row <= EXP_DAILY_END) {
      setDateIfEmpty(sheet, row, EXP_DATE_COL);
    }
    if (col === INC_AMT_COL && Number(val) > 0 &&
        row >= INC_DAILY_START && row <= INC_DAILY_END) {
      setDateIfEmpty(sheet, row, INC_DATE_COL);
    }
  }

  // Логика журнала долгов
  if (name === JOURNAL_SHEET && col === J_STATUS) {
    if (val === "Возвращён") {
      handleFullReturn(sheet, row);
    } else if (val === "Частично") {
      handlePartialReturn(sheet, row);
    } else if (val === "Активен" && old && old !== "Активен" && old !== "") {
      handleRevertToActive(sheet, row, old);
    }
  }
}

function setDateIfEmpty(sheet, row, dateCol) {
  const cell = sheet.getRange(row, dateCol);
  if (!cell.getValue()) {
    cell.setValue(new Date());
    cell.setNumberFormat("DD.MM.YYYY");
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ПОЛНЫЙ ВОЗВРАТ ДОЛГА
// ═══════════════════════════════════════════════════════════════════════════════
function handleFullReturn(journalSheet, row) {
  const d = readDebtRow(journalSheet, row);
  if (!d.name || d.amount <= 0) return;

  const targetMonth = monthFromDate(d.returnDate);
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const targetSheet = ss.getSheetByName(targetMonth);

  if (!targetSheet) {
    SpreadsheetApp.getUi().alert(
      `⚠️ Лист "${targetMonth}" скрыт.\n\nМеню → 💰 Финансы → Показать все месяцы\nЗатем поменяйте статус снова.`
    );
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }

  const entryType = d.type === "Мне должны" ? "income" : "expense";
  const entryDate = d.returnDate instanceof Date ? d.returnDate : new Date();
  const note = `Возврат долга: ${d.name}${d.desc ? " — " + d.desc : ""}`;

  const ok = writeDailyEntry(targetSheet, entryType, entryDate, d.name, "Возврат долга", d.amount, note);

  if (ok) {
    journalSheet.getRange(row, J_NOTE).setValue(
      `Закрыт ${fmt(new Date())}. Сумма: ${money(d.amount)}`
    );
    journalSheet.getRange(row, J_NUM, 1, J_NOTE - J_NUM + 1).setBackground("#0D2F1A");
    writeReturnHistory(d.name, d.type, d.amount, 0, d.amount, "Полностью", d.desc, d.recordDate instanceof Date ? fmt(d.recordDate) : "");

    const dir = d.type === "Мне должны" ? "поступления" : "расходы";
    SpreadsheetApp.getUi().alert(
      `✅ Записано в ${dir}!\n\nМесяц: ${targetMonth}\n` +
      `${d.type === "Мне должны" ? "От кого" : "Кому"}: ${d.name}\n` +
      `Сумма: ${money(d.amount)}`
    );
    refreshMonthDebts(targetSheet, targetMonth);
  } else {
    SpreadsheetApp.getUi().alert("⚠️ Нет свободных строк в ежедневных операциях.");
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ЧАСТИЧНЫЙ ВОЗВРАТ
// Оригинальная строка → статус "Частично", сумма уменьшается на выплаченное
// Новая строка с остатком → статус "Активен"
// ═══════════════════════════════════════════════════════════════════════════════
function handlePartialReturn(journalSheet, row) {
  const d = readDebtRow(journalSheet, row);
  if (!d.name || d.amount <= 0) return;

  const ui = SpreadsheetApp.getUi();

  // Спросить сколько вернули
  const paidResp = ui.prompt(
    "💳 Частичный возврат",
    `Долг: ${d.name} — ${money(d.amount)}\n\nСколько вернули / вернул (₸)?`,
    ui.ButtonSet.OK_CANCEL
  );
  if (paidResp.getSelectedButton() !== ui.Button.OK) {
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }
  const paid = Number(paidResp.getResponseText().replace(/\s/g, ""));
  if (!paid || paid <= 0 || paid >= d.amount) {
    ui.alert("⚠️ Некорректная сумма. Должно быть больше 0 и меньше " + money(d.amount));
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }

  // Спросить когда ждать следующий платёж
  const dateResp = ui.prompt(
    "📅 Следующий платёж",
    `Остаток: ${money(d.amount - paid)}\n\nКогда ожидать следующий платёж?\n(DD.MM.YYYY или оставь пустым)`,
    ui.ButtonSet.OK_CANCEL
  );
  if (dateResp.getSelectedButton() !== ui.Button.OK) {
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }

  const remain = d.amount - paid;
  const nextDateStr = dateResp.getResponseText().trim();
  const nextDate = nextDateStr ? parseDate(nextDateStr) : null;
  const targetMonth = monthFromDate(d.returnDate);
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const targetSheet = ss.getSheetByName(targetMonth);

  if (!targetSheet) {
    ui.alert(`⚠️ Лист "${targetMonth}" скрыт. Покажите его и повторите.`);
    journalSheet.getRange(row, J_STATUS).setValue("Активен");
    return;
  }

  // Записать выплаченную сумму в ежедневные операции
  const entryType = d.type === "Мне должны" ? "income" : "expense";
  const note = `Частичный возврат (${money(paid)} из ${money(d.amount)}): ${d.name}`;
  writeDailyEntry(targetSheet, entryType,
    d.returnDate instanceof Date ? d.returnDate : new Date(),
    d.name, "Возврат долга", paid, note);

  // Обновить оригинальную строку:
  // статус = "Частично", сумма = уплаченная, примечание
  journalSheet.getRange(row, J_AMOUNT).setValue(paid);
  journalSheet.getRange(row, J_NOTE).setValue(
    `Частично: ${money(paid)} получено ${fmt(new Date())}. Остаток: ${money(remain)}`
  );
  // Статус остаётся "Частично" (уже установлен пользователем)
  journalSheet.getRange(row, J_NUM, 1, J_NOTE - J_NUM + 1).setBackground("#2D2A0D");

  // Создать новую строку с остатком → статус "Активен"
  const emptyRow = findEmptyDebtRow(journalSheet);
  if (emptyRow) {
    journalSheet.getRange(emptyRow, J_NUM).setValue(emptyRow - J_START + 1);
    journalSheet.getRange(emptyRow, J_TYPE).setValue(d.type);
    journalSheet.getRange(emptyRow, J_NAME).setValue(d.name);
    journalSheet.getRange(emptyRow, J_DESC).setValue(d.desc || "");
    journalSheet.getRange(emptyRow, J_AMOUNT).setValue(remain);
    journalSheet.getRange(emptyRow, J_REC).setValue(new Date()).setNumberFormat("DD.MM.YYYY");
    if (nextDate) {
      journalSheet.getRange(emptyRow, J_RET).setValue(nextDate).setNumberFormat("DD.MM.YYYY");
    }
    journalSheet.getRange(emptyRow, J_STATUS).setValue("Активен");
    journalSheet.getRange(emptyRow, J_NOTE).setValue(
      `Остаток от частичного возврата ${fmt(new Date())}`
    );
  }

  const dir = d.type === "Мне должны" ? "поступления" : "расходы";
  ui.alert(
    `✅ Частичный возврат записан!\n\n` +
    `Записано в ${dir}: ${money(paid)}\n` +
    `Остаток ${money(remain)} добавлен новой строкой (Активен)\n` +
    `Текущая строка помечена как Частично\n` +
    `${nextDate ? "Следующий платёж: " + fmt(nextDate) : ""}`
  );

  refreshMonthDebts(targetSheet, targetMonth);
}

// ═══════════════════════════════════════════════════════════════════════════════
// ЗАЩИТА ОТ СЛУЧАЙНОГО СБРОСА СТАТУСА
// ═══════════════════════════════════════════════════════════════════════════════
function handleRevertToActive(journalSheet, row, previousStatus) {
  const d = readDebtRow(journalSheet, row);
  const ui = SpreadsheetApp.getUi();

  const resp = ui.alert(
    "⚠️ Подтверждение",
    `Вы сбрасываете статус "${d.name}" обратно на Активен.\n\n` +
    `Запись в доходах/расходах уже создана — её нужно удалить вручную.\n\n` +
    `Продолжить?`,
    ui.ButtonSet.YES_NO
  );

  if (resp !== ui.Button.YES) {
    journalSheet.getRange(row, J_STATUS).setValue(previousStatus);
  } else {
    journalSheet.getRange(row, J_NUM, 1, J_NOTE - J_NUM + 1).setBackground("#21262D");
    journalSheet.getRange(row, J_NOTE).setValue(
      `⚠️ Статус отменён вручную ${fmt(new Date())}`
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ЗАПИСЬ В ЕЖЕДНЕВНЫЕ ОПЕРАЦИИ (точные координаты)
// ═══════════════════════════════════════════════════════════════════════════════
function writeDailyEntry(sheet, type, date, description, category, amount, note) {
  const isExp  = type === "expense";
  const sRow   = isExp ? EXP_DAILY_START : INC_DAILY_START;
  const eRow   = isExp ? EXP_DAILY_END   : INC_DAILY_END;
  const dateC  = isExp ? EXP_DATE_COL    : INC_DATE_COL;
  const descC  = isExp ? EXP_DESC_COL    : INC_DESC_COL;
  const catC   = isExp ? EXP_CAT_COL2    : INC_CAT_COL2;
  const amtC   = isExp ? EXP_AMT_COL     : INC_AMT_COL;
  const noteC  = isExp ? EXP_NOTE_COL    : INC_NOTE_COL;

  // Читаем колонку суммы и описания одним запросом
  const amtVals  = sheet.getRange(sRow, amtC,  eRow - sRow + 1, 1).getValues();
  const descVals = sheet.getRange(sRow, descC, eRow - sRow + 1, 1).getValues();

  for (let i = 0; i < amtVals.length; i++) {
    const existAmt  = Number(amtVals[i][0])  || 0;
    const existDesc = String(descVals[i][0]  || "").trim();
    if (existAmt === 0 && existDesc === "") {
      const r = sRow + i;
      sheet.getRange(r, dateC).setValue(date).setNumberFormat("DD.MM.YYYY");
      sheet.getRange(r, descC).setValue(description);
      sheet.getRange(r, catC).setValue(category);
      sheet.getRange(r, amtC).setValue(amount);
      sheet.getRange(r, noteC).setValue(note);
      Logger.log(`✅ Запись в строку ${r} (${type})`);
      return true;
    }
  }
  Logger.log("❌ Нет свободных строк для " + type);
  return false;
}

function writeReturnHistory(name, type, paid, remain, originalAmount, returnType, description, recordDate) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(HISTORY_SHEET);
  if (!sheet) {
    sheet = ss.insertSheet(HISTORY_SHEET);
    setupHistorySheet(sheet);
  }
  const MONEY_FMT = '#,##0 "₸"';
  const lastRow = Math.max(sheet.getLastRow(), 1) + 1;
  sheet.getRange(lastRow, 1).setValue(new Date()).setNumberFormat("DD.MM.YYYY HH:mm");
  sheet.getRange(lastRow, 2).setValue(name);
  sheet.getRange(lastRow, 3).setValue(description || "");
  sheet.getRange(lastRow, 4).setValue(type);
  sheet.getRange(lastRow, 5).setValue(returnType);
  sheet.getRange(lastRow, 6).setValue(originalAmount).setNumberFormat(MONEY_FMT);
  sheet.getRange(lastRow, 7).setValue(paid).setNumberFormat(MONEY_FMT);
  sheet.getRange(lastRow, 8).setValue(remain).setNumberFormat(MONEY_FMT);
  sheet.getRange(lastRow, 9).setValue(recordDate || "");
  const bg = lastRow % 2 === 0 ? "#0D1117" : "#161B22";
  const textColor = returnType === "Полностью" ? "#3FB950" : "#E3B341";
  sheet.getRange(lastRow, 1, 1, 9).setBackground(bg).setFontColor("#C9D1D9");
  sheet.getRange(lastRow, 5).setFontColor(textColor).setFontWeight("bold");
}

function setupHistorySheet(sheet) {
  const headers = [
    "📅 Дата возврата", "👤 Имя", "📝 Описание долга",
    "Тип долга", "Статус возврата",
    "💰 Изначальная сумма", "✅ Возвращено", "📋 Остаток",
    "📆 Дата займа"
  ];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length)
    .setBackground("#1C2333")
    .setFontColor("#E3B341")
    .setFontWeight("bold")
    .setFontSize(10)
    .setHorizontalAlignment("center")
    .setBorder(false, false, true, false, false, false, "#E3B341", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  sheet.setColumnWidth(1, 140); sheet.setColumnWidth(2, 120);
  sheet.setColumnWidth(3, 200); sheet.setColumnWidth(4, 120);
  sheet.setColumnWidth(5, 130); sheet.setColumnWidth(6, 150);
  sheet.setColumnWidth(7, 130); sheet.setColumnWidth(8, 110);
  sheet.setColumnWidth(9, 130);
  sheet.setFrozenRows(1);
}

// ═══════════════════════════════════════════════════════════════════════════════
// ОБНОВЛЕНИЕ ДОЛГОВ В МЕСЯЧНЫХ ЛИСТАХ
// Использует точные координаты из диагностики
// ═══════════════════════════════════════════════════════════════════════════════
function refreshMonthDebts(sheet, monthName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const journal = ss.getSheetByName(JOURNAL_SHEET);
  if (!journal || !sheet) return;

  // Читаем все данные журнала
  const jData = journal.getRange(J_START, J_TYPE, J_END - J_START + 1, J_NOTE - J_TYPE + 1).getValues();

  const meDebts = [];
  const iDebts  = [];

  jData.forEach(row => {
    const type   = String(row[0] || "").trim(); // C
    const name   = String(row[1] || "").trim(); // D
    const amount = Number(row[3]) || 0;          // F
    const retD   = row[5];                       // H — дата возврата
    const status = String(row[6] || "").trim();  // I

    if (!type || !name || amount <= 0) return;
    if (status === "Возвращён") return;

    // Определить месяц возврата
    let retMonth = "";
    if (retD instanceof Date && !isNaN(retD)) {
      retMonth = MONTHS[retD.getMonth()];
    } else if (typeof retD === "string" && MONTHS.includes(retD.trim())) {
      retMonth = retD.trim(); // совместимость со старым форматом
    }

    if (retMonth !== monthName) return;

    const retStr = retD instanceof Date ? fmt(retD) : String(retD || "");
    const entry  = { name, amount, retStr, status };

    if (type === "Мне должны")      meDebts.push(entry);
    else if (type === "Я должен")   iDebts.push(entry);
  });

  // Заполнить "МНЕ ДОЛЖНЫ" (строки 7-14)
  fillBlock(sheet, DME_DATA_START, DME_DATA_END, meDebts, true);

  // Заполнить "Я ДОЛЖЕН" (строки 19-26)
  fillBlock(sheet, DI_DATA_START, DI_DATA_END, iDebts, false);

  Logger.log(`✅ Долги обновлены в листе ${monthName}: ${meDebts.length} мне, ${iDebts.length} я`);
}

function fillBlock(sheet, startRow, endRow, debts, isIncoming) {
  const CFMT = '#,##0 "₸";-#,##0 "₸";"-"';
  const color = isIncoming ? "#3FB950" : "#F85149";

  for (let i = startRow; i <= endRow; i++) {
    const idx = i - startRow;
    const debt = debts[idx];

    // Имя
    const nameCell = sheet.getRange(i, DEBT_NAME_COL);
    nameCell.setValue(debt ? debt.name : "—");
    nameCell.setFontColor(debt ? "#C9D1D9" : "#8B949E");

    // Сумма
    const amtCell = sheet.getRange(i, DEBT_AMT_COL);
    amtCell.setValue(debt ? debt.amount : 0);
    amtCell.setNumberFormat(CFMT);
    amtCell.setFontColor(debt ? color : "#8B949E");

    // Дата/статус
    const dateCell = sheet.getRange(i, DEBT_DATE_COL);
    if (debt) {
      dateCell.setValue(debt.retStr || "—");
      // Если долг частично погашен — подсветить жёлтым
      if (debt.status === "Частично") {
        sheet.getRange(i, DEBT_NAME_COL, 1, 3).setBackground("#2D2A0D");
      } else {
        sheet.getRange(i, DEBT_NAME_COL, 1, 3).setBackground("#21262D");
      }
    } else {
      dateCell.setValue("—");
      sheet.getRange(i, DEBT_NAME_COL, 1, 3).setBackground("#21262D");
    }
    dateCell.setFontColor("#8B949E");
  }
}

function checkOverdueDebtsAuto() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const journal = ss.getSheetByName(JOURNAL_SHEET);
  if (!journal) return;
  const today = new Date(); today.setHours(0,0,0,0);
  const data = journal.getRange(J_START, J_TYPE, J_END-J_START+1, J_NOTE-J_TYPE+1).getValues();
  data.forEach((row,i) => {
    const status=row[6], retDate=row[5];
    if (status==="Возвращён"||!(retDate instanceof Date)||isNaN(retDate)) return;
    const ret=new Date(retDate); ret.setHours(0,0,0,0);
    if (ret<today) journal.getRange(i+J_START,J_NUM,1,J_NOTE-J_NUM+1).setBackground("#2D1010");
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// ТРИГГЕРЫ
// ═══════════════════════════════════════════════════════════════════════════════
function setupTriggers() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("manageSheetVisibility")
    .timeBased().everyDays(1).atHour(0).create();
  ScriptApp.newTrigger("checkOverdueDebtsAuto")
    .timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(9).create();
  ScriptApp.newTrigger("refreshAllMonthDebts")
    .timeBased().everyDays(1).atHour(1).create();
  Logger.log("✅ Триггеры установлены");
}

// ═══════════════════════════════════════════════════════════════════════════════
// УТИЛИТЫ
// ═══════════════════════════════════════════════════════════════════════════════
function readDebtRow(sheet, row) {
  const data = sheet.getRange(row, J_TYPE, 1, J_NOTE - J_TYPE + 1).getValues()[0];
  return {
    type:       String(data[0] || "").trim(),
    name:       String(data[1] || "").trim(),
    desc:       String(data[2] || "").trim(),
    amount:     Number(data[3]) || 0,
    recordDate: data[4],
    returnDate: data[5],
    status:     String(data[6] || "").trim(),
    note:       String(data[7] || "").trim()
  };
}

function monthFromDate(d) {
  if (d instanceof Date && !isNaN(d)) return MONTHS[d.getMonth()];
  return MONTHS[new Date().getMonth()];
}

function findEmptyDebtRow(sheet) {
  const data = sheet.getRange(J_START, J_TYPE, J_END - J_START + 1, 1).getValues();
  for (let i = 0; i < data.length; i++) {
    if (!String(data[i][0]).trim()) return J_START + i;
  }
  return null;
}

function parseDate(str) {
  const p = str.split(".");
  if (p.length !== 3) return null;
  const d = new Date(Number(p[2]), Number(p[1])-1, Number(p[0]));
  return isNaN(d) ? null : d;
}

function fmt(date) {
  if (!date || !(date instanceof Date)) return "";
  return Utilities.formatDate(date, Session.getScriptTimeZone(), "dd.MM.yyyy");
}

function money(amount) {
  if (!amount) return "0 ₸";
  return new Intl.NumberFormat("ru-RU").format(Math.round(amount)) + " ₸";
}

