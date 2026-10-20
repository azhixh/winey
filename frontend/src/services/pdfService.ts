/**
 * PDF Export & Print Service for BQAS Result Reports
 */

export function exportReportToPDF(): void {
  // Triggers native browser print dialog styled via @media print in global.css
  window.print();
}
