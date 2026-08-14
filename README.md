# Notification Service

Sistema de notificaciones asincronas con cola Redis, workers ARQ, reintentos automaticos y dead letter queue.

## Stack

- **FastAPI** — API REST con documentacion automatica
- **ARQ** — Motor de workers asincronos sobre Redis
- **Redis** — Cola de mensajes entre la API y los workers
- **PostgreSQL** — Persistencia de notificaciones y su historial de estados
- **Docker Compose** — Contenedorizacion completa incluyendo el worker
- **GitHub Actions** — CI/CD con self-hosted runner

## Arquitectura

```
Cliente POST /notifications/
        ↓
API valida y guarda en PostgreSQL (status: pending)
        ↓
API encola tarea en Redis
        ↓
202 Accepted (respuesta inmediata al cliente)
        ↓
Worker ARQ lee la cola
        ↓
Procesa la notificacion
    ↓ exito  → status: delivered
    ↓ fallo  → reintenta cada 10s hasta 3 veces
    ↓ fallo permanente → status: failed (dead letter queue)
```

PostgreSQL guarda el historial completo — intentos, errores y timestamps. Si el worker falla definitivamente, el registro queda disponible para auditoria.

## Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `POST` | `/notifications/` | Crear notificacion (202 Accepted) |
| `GET` | `/notifications/` | Listar notificaciones con filtro por estado |
| `GET` | `/notifications/{id}` | Ver estado de una notificacion |
| `GET` | `/health` | Estado del servicio |

## Estados de una notificacion

| Estado | Descripcion |
|--------|-------------|
| `pending` | Encolada, esperando worker |
| `processing` | Worker ejecutando |
| `delivered` | Procesada exitosamente |
| `failed` | Fallo definitivo tras 3 intentos |

## Probarlo ahora

**Crear una notificacion:**
```bash
curl -X POST https://TU_DOMINIO/notifications/ \
  -H "Content-Type: application/json" \
  -d '{"recipient": "usuario@email.com", "message": "Bienvenido al sistema"}'
```

**Ver su estado:**
```bash
curl https://TU_DOMINIO/notifications/1
```

**Listar solo las fallidas:**
```bash
curl https://TU_DOMINIO/notifications/?status=failed
```

**Interfaz web:**
```
https://TU_DOMINIO/
```

## Correr localmente

**Requisitos:** Docker y Docker Compose instalados.

```bash
# 1. Clonar el repositorio
git clone git@github.com:JJrendon29/notification-service.git
cd notification-service

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 3. Levantar todos los servicios incluyendo el worker
docker compose up -d --build

# 4. Verificar que funciona
curl http://localhost:8003/health
```

## Estructura

```
notification-service/
├── app/
│   ├── models/          # Modelo de base de datos
│   ├── schemas/         # Schemas de validacion (EmailStr)
│   ├── routers/         # Endpoints de la API
│   ├── workers/         # Worker ARQ con logica de reintentos
│   ├── config.py        # Configuracion centralizada
│   ├── database.py      # Conexion a PostgreSQL
│   └── main.py          # Punto de entrada
├── static/              # Interfaz web
│   ├── css/style.css
│   └── js/app.js
├── .github/
│   └── workflows/       # Pipeline CI/CD
├── Dockerfile
├── docker-compose.yml   # Incluye api + worker + db + cache
└── requirements.txt
```

## Decisiones de diseno

**202 Accepted en vez de 200 OK** — el contrato honesto con el cliente. La notificacion fue recibida y encolada, no procesada todavia.

**Re-encolado manual con delay** — el worker reencola la tarea con 10 segundos de espera entre reintentos en vez de depender del mecanismo automatico de ARQ. Mas control sobre el backoff.

**Dead letter queue en PostgreSQL** — las notificaciones que fallan definitivamente no desaparecen. Quedan con status `failed` y el ultimo error registrado para auditoria.

**Worker como contenedor separado** — misma imagen Docker que la API, diferente comando. Escala independientemente sin afectar a la API.

## CI/CD

Cada push a `main` ejecuta automaticamente:

1. Deploy con Docker Compose incluyendo el worker
