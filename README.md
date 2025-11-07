# Sistema de Reservas de Canchas Deportivas 🏟️⚽

**Trabajo Práctico Integrador - DAO**  
**Grupo G25**

## Integrantes
- Aybar Laura Noelia (92472)
- Correa, Maria Valentina (400655)
- Golbert Lautaro (400660)
- Lopez Morales, Pilar (400390)
- Pérez, Facundo (401067)

## Descripción del Proyecto

Este sistema permite a los **clientes** gestionar reservas de canchas deportivas de manera simple y eficiente. A diferencia de un sistema de administración, este está diseñado desde la **perspectiva del usuario que quiere reservar una cancha**.

### ¿Qué puede hacer un cliente?

✅ **Registrarse** en el sistema con sus datos personales  
✅ **Ver canchas disponibles** con sus características (tipo de deporte, precio, horarios)  
✅ **Verificar disponibilidad** antes de reservar  
✅ **Hacer reservas** de canchas en fechas y horarios específicos  
✅ **Agregar servicios adicionales** (pelotas, buffet, estacionamiento, etc.)  
✅ **Ver sus propias reservas** y su estado (Pendiente, Confirmada, Cancelada)  
✅ **Cancelar reservas** si es necesario  
✅ **Registrar pagos** con diferentes métodos  
✅ **Ver estadísticas** personales (total gastado, cancha favorita, etc.)

## Tecnologías Utilizadas

- **Python 3.10+**
- **Flask** - Framework web
- **SQLAlchemy** - ORM para base de datos
- **SQLite** - Base de datos (ideal para desarrollo y demos)
- **Swagger UI** - Documentación interactiva de la API

## Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/golbertlautaro-cell/Tp-Dao.git
cd Tp-Dao
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
```

Activar el entorno:
- **Windows**: `venv\Scripts\activate`
- **Linux/Mac**: `source venv/bin/activate`

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
```bash
python trabajo_practico.py
```

El servidor se iniciará en `http://localhost:5000`

## Documentación de la API

Una vez que el servidor esté corriendo, puedes acceder a la documentación interactiva de Swagger en:

🔗 **http://localhost:5000/api/docs**

Desde ahí podrás:
- Ver todos los endpoints disponibles
- Probar las peticiones directamente desde el navegador
- Ver ejemplos de requests y responses

## Endpoints Principales

### 👤 Gestión de Cliente
- `POST /api/cliente/registro` - Registrarse como nuevo cliente
- `GET /api/cliente/{id}` - Ver mi perfil
- `PUT /api/cliente/{id}` - Actualizar mis datos

### 🏟️ Consulta de Canchas
- `GET /api/canchas` - Listar todas las canchas
- `GET /api/canchas/{id}` - Ver detalles de una cancha
- `GET /api/canchas/{id}/disponibilidad` - Verificar si está disponible

### 📅 Reservas
- `POST /api/reservas` - Crear nueva reserva
- `GET /api/cliente/{id}/reservas` - Ver mis reservas
- `GET /api/reservas/{id}` - Detalle de una reserva
- `PUT /api/reservas/{id}/cancelar` - Cancelar mi reserva

### 🎁 Servicios Adicionales
- `GET /api/servicios` - Ver servicios disponibles
- `POST /api/reservas/{id}/servicios` - Agregar servicio a mi reserva

### 💰 Pagos
- `GET /api/metodos-pago` - Ver métodos de pago
- `POST /api/reservas/{id}/pago` - Registrar un pago
- `GET /api/cliente/{id}/pagos` - Ver mi historial de pagos

### 📊 Estadísticas
- `GET /api/cliente/{id}/estadisticas` - Ver mis estadísticas de uso

## Estructura del Proyecto

```
tpDao/
│
├── trabajo_practico.py      # Archivo principal con toda la lógica
├── requirements.txt         # Dependencias del proyecto
├── README.md               # Este archivo
├── static/
│   └── swagger.json        # Especificación OpenAPI para Swagger
└── reservas_cliente.db     # Base de datos SQLite (se crea automáticamente)
```

## Modelo de Datos

El sistema maneja las siguientes entidades:

- **Cliente**: Usuario que hace reservas
- **Cancha**: Cancha deportiva disponible para reservar
- **HorarioDisponible**: Horarios en que cada cancha está disponible
- **Reserva**: Reserva de una cancha por un cliente
- **EstadoReserva**: Estados posibles (Pendiente, Confirmada, Cancelada)
- **ServicioAdicional**: Servicios extra que se pueden contratar
- **ReservaServicio**: Relación entre reservas y servicios
- **MetodoPago**: Formas de pago disponibles
- **Pago**: Registro de pagos realizados

## Datos de Demostración

Al ejecutar por primera vez, el sistema crea automáticamente:
- 6 canchas de ejemplo (Fútbol 5, Fútbol 7, Paddle, Tenis)
- Horarios disponibles (Lunes a Domingo, 9:00 a 23:00)
- 5 servicios adicionales
- Estados de reserva (Pendiente, Confirmada, Cancelada)
- Métodos de pago (Efectivo, Tarjetas, Transferencia, MercadoPago)
- Un cliente de ejemplo (DNI: 12345678)

## Ejemplos de Uso

### Registrar un nuevo cliente
```bash
curl -X POST http://localhost:5000/api/cliente/registro \
  -H "Content-Type: application/json" \
  -d '{
    "dni": "87654321",
    "nombre": "María",
    "apellido": "González",
    "telefono": "1198765432",
    "email": "maria@example.com"
  }'
```

### Ver canchas disponibles
```bash
curl http://localhost:5000/api/canchas
```

### Crear una reserva
```bash
curl -X POST http://localhost:5000/api/reservas \
  -H "Content-Type: application/json" \
  -d '{
    "id_cliente": 1,
    "id_cancha": 1,
    "fecha_reserva": "2024-11-20",
    "hora_inicio": "18:00",
    "hora_fin": "19:00",
    "servicios_adicionales": [1, 4]
  }'
```

## Validaciones Implementadas

✅ No se pueden reservar fechas pasadas  
✅ El horario debe estar entre 09:00 y 23:00  
✅ No se permiten solapamientos de reservas  
✅ Los clientes deben estar activos  
✅ Las canchas deben estar activas  
✅ No se pueden agregar servicios a reservas canceladas  
✅ El DNI y email son únicos por cliente

## Características del Código

Este código fue diseñado para verse como **trabajo de estudiante universitario**, no como producción profesional:

- ✅ Comentarios explicativos en español
- ✅ Nombres de variables descriptivos
- ✅ Estructura clara y fácil de entender
- ✅ Docstrings en las funciones principales
- ✅ Separación por secciones con comentarios grandes
- ✅ Código más "didáctico" que optimizado
- ✅ Manejo básico de errores (no sobreingeniado)

## Notas Importantes

⚠️ Esta es una aplicación de **demostración educativa**. Para uso en producción sería necesario:
- Autenticación y autorización (JWT, OAuth, etc.)
- Validaciones más robustas
- Manejo de errores más completo
- Base de datos más escalable (PostgreSQL, MySQL)
- Deploy en un servidor real
- HTTPS y seguridad adicional
- Tests unitarios y de integración

## Contacto

Para consultas sobre el proyecto:
- Email del grupo: grupo25@universidad.edu.ar
- GitHub: https://github.com/golbertlautaro-cell/Tp-Dao

---

**Desarrollo de Aplicaciones con Objetos - 2024**
