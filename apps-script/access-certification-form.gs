/**
 * IAM Access Certification — Apps Script
 * Vinculado a la Google Sheet "IAM-Access-Certification"
 *
 * Flujo: cada fila representa un hallazgo de auditoría (extraído de Azure SQL).
 * Un revisor selecciona Decision = Aprobado/Revocado en la columna F.
 * El script auto-registra quién y cuándo revisó (trazabilidad SOX),
 * y permite generar un resumen de % de revisión completada.
 */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Auditoría IAM')
    .addItem('Generar resumen de revisión', 'resumenRevision')
    .addToUi();

  aplicarValidacionDecision();
}

function aplicarValidacionDecision() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  const rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['Pendiente', 'Aprobado', 'Revocado'])
    .setAllowInvalid(false)
    .build();

  sheet.getRange(2, 6, lastRow - 1, 1).setDataValidation(rule); // columna F = Decision
}

function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  const col = e.range.getColumn();
  const row = e.range.getRow();

  // Columna F = Decision (6)
  if (col === 6 && row > 1) {
    const decision = e.range.getValue();
    if (decision === 'Aprobado' || decision === 'Revocado') {
      sheet.getRange(row, 7).setValue(Session.getActiveUser().getEmail()); // Revisado_Por
      sheet.getRange(row, 8).setValue(new Date());                        // Fecha_Revision
    }
  }
}

function resumenRevision() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
  const data = sheet.getDataRange().getValues();
  let pendientes = 0, aprobados = 0, revocados = 0;

  for (let i = 1; i < data.length; i++) {
    const decision = data[i][5];
    if (decision === 'Aprobado') aprobados++;
    else if (decision === 'Revocado') revocados++;
    else pendientes++;
  }

  SpreadsheetApp.getUi().alert(
    `📋 Resumen de revisión\n\nPendientes: ${pendientes}\nAprobados: ${aprobados}\nRevocados: ${revocados}\n\n% Completado: ${(((aprobados+revocados)/(data.length-1))*100).toFixed(1)}%`
  );
}