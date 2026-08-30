export const FILE_ICONS = {
  '.docx': '📄',
  '.pdf': '📄',
  '.pptx': '📊',
  '.zip': '📦',
  '.mp4': '🎥',
  '.png': '🖼️',
  '.jpg': '🖼️',
  '.jpeg': '🖼️',
}

export function getFileIcon(filename) {
  const ext = '.' + filename.split('.').pop().toLowerCase()
  return FILE_ICONS[ext] || '📎'
}

export function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
