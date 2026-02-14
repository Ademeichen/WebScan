export function formatDate(date) {
  if (!date) return '-';
  
  // 如果是字符串且不包含时区信息(Z或+)，假设是UTC时间
  // 后端数据库通常存UTC，如果返回格式是 "YYYY-MM-DD HH:mm:ss" 且没带时区
  // 浏览器会当成本地时间解析，导致时间偏差
  let dateStr = date;
  if (typeof date === 'string' && !date.includes('Z') && !date.includes('+') && /^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$/.test(date)) {
    dateStr = date.replace(' ', 'T') + 'Z';
  }

  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return date;
  return d.toLocaleString();
}
