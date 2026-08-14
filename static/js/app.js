let currentFilter = 'all'
let refreshInterval = null

function formatDate(iso) {
  return new Date(iso).toLocaleString('es-CO', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

async function sendNotification() {
  const recipient = document.getElementById('recipient-input').value.trim()
  const message = document.getElementById('message-input').value.trim()
  const btn = document.getElementById('send-btn')
  const responseBox = document.getElementById('response-box')
  const responseStatus = document.getElementById('response-status')
  const responseDetail = document.getElementById('response-detail')
  const errorMsg = document.getElementById('error-msg')

  responseBox.classList.add('hidden')
  errorMsg.classList.add('hidden')

  if (!recipient || !message) {
    errorMsg.textContent = 'Completá el destinatario y el mensaje.'
    errorMsg.classList.remove('hidden')
    return
  }

  if (!isValidEmail(recipient)) {
  errorMsg.textContent = 'Ingresá un email válido.'
  errorMsg.classList.remove('hidden')
  return
  }

  btn.disabled = true
  btn.textContent = 'Enviando...'

  try {
    const res = await fetch('/notifications/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient, message })
    })

    const data = await res.json()

    if (!res.ok) {
      errorMsg.textContent = data.detail || 'Error al enviar.'
      errorMsg.classList.remove('hidden')
      return
    }

    responseStatus.textContent = '202 Accepted — notificación encolada'
    responseDetail.textContent =
      `id: ${data.id}  |  status: ${data.status}  |  recipient: ${data.recipient}`
    responseBox.classList.remove('hidden')

    document.getElementById('recipient-input').value = ''
    document.getElementById('message-input').value = ''

    loadNotifications()

  } catch (e) {
    errorMsg.textContent = 'No se pudo conectar con el servidor.'
    errorMsg.classList.remove('hidden')
  } finally {
    btn.disabled = false
    btn.textContent = 'Enviar notificación'
  }
}

async function loadNotifications() {
  const params = currentFilter !== 'all' ? `?status=${currentFilter}` : ''

  try {
    const res = await fetch(`/notifications/${params}`)
    const data = await res.json()

    const list = document.getElementById('notifications-list')
    const empty = document.getElementById('empty-state')

    if (!data.length) {
      list.innerHTML = ''
      empty.classList.remove('hidden')
      return
    }

    empty.classList.add('hidden')
    list.innerHTML = data.slice().reverse().map(n => `
      <div class="notification-item">
        <div>
          <div class="notif-recipient">${escapeHtml(n.recipient)}</div>
          <div class="notif-message">${escapeHtml(n.message)}</div>
          <div class="notif-meta">
            <span>id: ${n.id}</span>
            <span>intentos: ${n.attempts}</span>
            <span>creado: ${formatDate(n.created_at)}</span>
            <span>actualizado: ${formatDate(n.updated_at)}</span>
            ${n.last_error ? `<span style="color:#F85149">error: ${escapeHtml(n.last_error)}</span>` : ''}
          </div>
        </div>
        <span class="status-badge status-${n.status}">${n.status}</span>
      </div>
    `).join('')

  } catch (e) {
    console.error('Error cargando notificaciones:', e)
  }
}

function setFilter(btn, status) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'))
  btn.classList.add('active')
  currentFilter = status
  loadNotifications()
}

document.addEventListener('DOMContentLoaded', () => {
  loadNotifications()
  refreshInterval = setInterval(loadNotifications, 3000)

  document.getElementById('message-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') sendNotification()
  })
})
