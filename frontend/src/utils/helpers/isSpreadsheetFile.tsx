export const isSpreadsheetFile = (type: string, name: string): boolean => {
  return type === 'text/csv' ||
    type === 'application/vnd.ms-excel' ||
    type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
    name.endsWith('.csv') ||
    name.endsWith('.xls') ||
    name.endsWith('.xlsx');
};