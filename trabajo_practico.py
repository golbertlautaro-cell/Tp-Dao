# Trabajo Práctico Integrador - DAO
# Sistema de Reservas de Canchas Deportivas
# Grupo G25 - Desarrollo desde la perspectiva del CLIENTE
# 
# Este sistema permite a los CLIENTES:
# - Registrarse en el sistema
# - Ver canchas disponibles
# - Hacer reservas de canchas
# - Consultar sus propias reservas
# - Agregar servicios adicionales
# - Ver el estado de sus pagos

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
from decimal import Decimal
import os

# ==============================================================================
# CONFIGURACIÓN INICIAL
# ==============================================================================

app = Flask(__name__)

# Config de la base de datos SQLite (más fácil para trabajos prácticos)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "reservas_cliente.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave-secreta-tp-dao-2024'  # En producción esto iría en variables de entorno

db = SQLAlchemy(app)

# ==============================================================================
# MODELOS DE BASE DE DATOS
# ==============================================================================

# Tabla de Clientes - Acá se registran los usuarios del sistema
class Cliente(db.Model):
    """
    Representa a un cliente que puede hacer reservas.
    Desde el punto de vista del cliente, esto es como su "perfil" en el sistema.
    """
    __tablename__ = 'clientes'
    
    id_cliente = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    activo = db.Column(db.Boolean, default=True)
    
    # Relación: un cliente puede tener muchas reservas
    reservas = db.relationship('Reserva', backref='cliente', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id_cliente': self.id_cliente,
            'dni': self.dni,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'telefono': self.telefono,
            'email': self.email,
            'activo': self.activo
        }


# Tabla de Canchas - Lo que el cliente puede reservar
class Cancha(db.Model):
    """
    Representa una cancha deportiva disponible para reservar.
    El cliente ve las canchas disponibles y elige cuál reservar.
    """
    __tablename__ = 'canchas'
    
    id_cancha = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo_deporte = db.Column(db.String(50))  # Fútbol, Tenis, Paddle, etc.
    superficie = db.Column(db.String(50))  # Césped, Sintético, Cemento, etc.
    precio_hora = db.Column(db.Numeric(10, 2), nullable=False)
    tiene_iluminacion = db.Column(db.Boolean, default=False)
    activa = db.Column(db.Boolean, default=True)
    
    # Relaciones
    reservas = db.relationship('Reserva', backref='cancha', lazy=True)
    horarios = db.relationship('HorarioDisponible', backref='cancha', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id_cancha': self.id_cancha,
            'nombre': self.nombre,
            'tipo_deporte': self.tipo_deporte,
            'superficie': self.superficie,
            'precio_hora': str(self.precio_hora),
            'tiene_iluminacion': self.tiene_iluminacion,
            'activa': self.activa
        }


# Horarios disponibles por cancha
class HorarioDisponible(db.Model):
    """
    Define qué días y horarios están disponibles para cada cancha.
    El cliente necesita saber cuándo puede reservar.
    """
    __tablename__ = 'horarios_disponibles'
    
    id_horario = db.Column(db.Integer, primary_key=True)
    id_cancha = db.Column(db.Integer, db.ForeignKey('canchas.id_cancha'), nullable=False)
    dia_semana = db.Column(db.String(20), nullable=False)  # Lunes, Martes, etc.
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id_horario': self.id_horario,
            'dia_semana': self.dia_semana,
            'hora_inicio': self.hora_inicio.strftime('%H:%M'),
            'hora_fin': self.hora_fin.strftime('%H:%M'),
            'disponible': self.disponible
        }


# Estados de reserva (Pendiente, Confirmada, Cancelada)
class EstadoReserva(db.Model):
    """
    Estados posibles de una reserva desde el punto de vista del cliente:
    - Pendiente: Acaba de solicitarla, esperando confirmación
    - Confirmada: Ya está aprobada, puede ir a jugar
    - Cancelada: Fue cancelada (por el cliente o por el sistema)
    """
    __tablename__ = 'estado_reserva'
    
    id_estado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    
    reservas = db.relationship('Reserva', backref='estado', lazy=True)
    
    def to_dict(self):
        return {
            'id_estado': self.id_estado,
            'nombre': self.nombre
        }


# Tabla principal de Reservas - Lo más importante para el cliente
class Reserva(db.Model):
    """
    Reserva de cancha hecha por un cliente.
    Contiene toda la información: qué cancha, cuándo, a qué hora, precio, etc.
    """
    __tablename__ = 'reservas'
    
    id_reserva = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    id_cancha = db.Column(db.Integer, db.ForeignKey('canchas.id_cancha'), nullable=False)
    id_estado = db.Column(db.Integer, db.ForeignKey('estado_reserva.id_estado'), nullable=False)
    fecha_reserva = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    precio_total = db.Column(db.Numeric(10, 2), default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones con servicios adicionales
    servicios = db.relationship('ReservaServicio', backref='reserva', lazy=True, cascade='all, delete-orphan')
    pagos = db.relationship('Pago', backref='reserva', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Método auxiliar para convertir a JSON fácilmente"""
        return {
            'id_reserva': self.id_reserva,
            'cliente': self.cliente.to_dict() if self.cliente else None,
            'cancha': self.cancha.to_dict() if self.cancha else None,
            'estado': self.estado.to_dict() if self.estado else None,
            'fecha_reserva': self.fecha_reserva.isoformat(),
            'hora_inicio': self.hora_inicio.strftime('%H:%M'),
            'hora_fin': self.hora_fin.strftime('%H:%M'),
            'precio_total': str(self.precio_total),
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }


# Servicios adicionales que el cliente puede contratar
class ServicioAdicional(db.Model):
    """
    Servicios extra que el cliente puede agregar a su reserva:
    - Alquiler de pelotas
    - Alquiler de raquetas
    - Servicio de buffet
    - etc.
    """
    __tablename__ = 'servicios_adicionales'
    
    id_servicio = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id_servicio': self.id_servicio,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'precio': str(self.precio),
            'activo': self.activo
        }


# Tabla intermedia entre Reserva y Servicio (relación N:M)
class ReservaServicio(db.Model):
    """
    Conecta las reservas con los servicios adicionales.
    Un cliente puede pedir varios servicios en una misma reserva.
    """
    __tablename__ = 'reserva_servicio'
    
    id_reserva_servicio = db.Column(db.Integer, primary_key=True)
    id_reserva = db.Column(db.Integer, db.ForeignKey('reservas.id_reserva'), nullable=False)
    id_servicio = db.Column(db.Integer, db.ForeignKey('servicios_adicionales.id_servicio'), nullable=False)
    cantidad = db.Column(db.Integer, default=1)
    
    servicio = db.relationship('ServicioAdicional', backref='reservas_servicios')


# Métodos de pago disponibles
class MetodoPago(db.Model):
    """
    Formas en que el cliente puede pagar:
    - Efectivo
    - Tarjeta de débito
    - Tarjeta de crédito
    - Transferencia bancaria
    - MercadoPago, etc.
    """
    __tablename__ = 'metodos_pago'
    
    id_metodo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    
    pagos = db.relationship('Pago', backref='metodo_pago', lazy=True)
    
    def to_dict(self):
        return {
            'id_metodo': self.id_metodo,
            'nombre': self.nombre
        }


# Pagos realizados por el cliente
class Pago(db.Model):
    """
    Registro de los pagos que hace el cliente para sus reservas.
    """
    __tablename__ = 'pagos'
    
    id_pago = db.Column(db.Integer, primary_key=True)
    id_reserva = db.Column(db.Integer, db.ForeignKey('reservas.id_reserva'), nullable=False)
    id_metodo = db.Column(db.Integer, db.ForeignKey('metodos_pago.id_metodo'), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(50), default='Pendiente')  # Pendiente, Aprobado, Rechazado
    
    def to_dict(self):
        return {
            'id_pago': self.id_pago,
            'id_reserva': self.id_reserva,
            'metodo_pago': self.metodo_pago.to_dict() if self.metodo_pago else None,
            'monto': str(self.monto),
            'fecha_pago': self.fecha_pago.isoformat() if self.fecha_pago else None,
            'estado': self.estado
        }


# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def validar_horario(fecha_reserva, hora_inicio, hora_fin):
    """
    Valida que el horario de reserva sea correcto:
    - Fecha no sea del pasado
    - Hora inicio sea menor que hora fin
    - Horario esté dentro del rango permitido (ej: 9:00 - 23:00)
    """
    # La fecha no puede ser del pasado
    if fecha_reserva < date.today():
        return False, "No se puede reservar una fecha pasada"
    
    # Hora inicio debe ser antes que hora fin
    if hora_inicio >= hora_fin:
        return False, "La hora de inicio debe ser anterior a la hora de fin"
    
    # Horario comercial: entre 9 AM y 11 PM
    if hora_inicio.hour < 9 or hora_fin.hour > 23:
        return False, "El horario debe estar entre las 09:00 y las 23:00"
    
    return True, "OK"


def verificar_disponibilidad(id_cancha, fecha, hora_inicio, hora_fin):
    """
    Verifica si la cancha está disponible en ese horario.
    Busca si hay otra reserva que se solape con el horario solicitado.
    """
    # Buscar reservas que se superpongan
    reservas_existentes = Reserva.query.filter(
        Reserva.id_cancha == id_cancha,
        Reserva.fecha_reserva == fecha,
        Reserva.hora_fin > hora_inicio,
        Reserva.hora_inicio < hora_fin
    ).first()
    
    if reservas_existentes:
        return False, "Ya hay una reserva en ese horario"
    
    return True, "Disponible"


def calcular_precio_reserva(id_cancha, hora_inicio, hora_fin, servicios_ids=None):
    """
    Calcula el precio total de la reserva:
    - Precio base por hora de la cancha
    - Precio de servicios adicionales
    """
    cancha = Cancha.query.get(id_cancha)
    if not cancha:
        return 0
    
    # Calcular duración en horas
    dt_inicio = datetime.combine(date.today(), hora_inicio)
    dt_fin = datetime.combine(date.today(), hora_fin)
    duracion_horas = (dt_fin - dt_inicio).total_seconds() / 3600
    
    # Precio base
    precio = Decimal(cancha.precio_hora) * Decimal(duracion_horas)
    
    # Agregar servicios adicionales
    if servicios_ids:
        for sid in servicios_ids:
            servicio = ServicioAdicional.query.get(sid)
            if servicio and servicio.activo:
                precio += Decimal(servicio.precio)
    
    return precio


# ==============================================================================
# ENDPOINTS DE LA API - PERSPECTIVA DEL CLIENTE
# ==============================================================================

# Ruta principal
@app.route('/')
def index():
    """Página de inicio - Redirige al dashboard del cliente"""
    return render_template('index.html')


# ==============================================================================
# RUTAS WEB (UI) - PERSPECTIVA DEL CLIENTE
# ==============================================================================

@app.route('/ui/dashboard')
def ui_dashboard():
    """Dashboard principal del cliente"""
    return render_template('dashboard.html')


@app.route('/ui/registro')
def ui_registro():
    """Formulario de registro de nuevo cliente"""
    return render_template('registro.html')


@app.route('/ui/canchas')
def ui_canchas():
    """Ver canchas disponibles"""
    return render_template('canchas.html')


@app.route('/ui/reservar')
def ui_reservar():
    """Formulario para hacer una reserva"""
    return render_template('reservar.html')


@app.route('/ui/mis-reservas')
def ui_mis_reservas():
    """Ver mis propias reservas"""
    return render_template('mis_reservas.html')


@app.route('/ui/perfil')
def ui_perfil():
    """Ver y editar mi perfil"""
    return render_template('perfil.html')


# ==============================================================================
# GESTIÓN DE PERFIL DEL CLIENTE
# ==============================================================================

@app.route('/api/cliente/registro', methods=['POST'])
def registro_cliente():
    """
    Endpoint para que un nuevo cliente se registre en el sistema.
    El cliente proporciona sus datos personales.
    """
    data = request.get_json()
    
    # Validar campos requeridos
    if not data or not data.get('dni') or not data.get('nombre') or not data.get('apellido'):
        return jsonify({'error': 'Faltan datos obligatorios: dni, nombre, apellido'}), 400
    
    # Verificar si el DNI ya existe
    cliente_existente = Cliente.query.filter_by(dni=data['dni']).first()
    if cliente_existente:
        return jsonify({'error': 'El DNI ya está registrado en el sistema'}), 409
    
    # Verificar si el email ya existe (si se proporciona)
    if data.get('email'):
        email_existente = Cliente.query.filter_by(email=data['email']).first()
        if email_existente:
            return jsonify({'error': 'El email ya está registrado'}), 409
    
    # Crear nuevo cliente
    try:
        nuevo_cliente = Cliente(
            dni=data['dni'],
            nombre=data['nombre'],
            apellido=data['apellido'],
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            activo=True
        )
        db.session.add(nuevo_cliente)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Cliente registrado exitosamente',
            'cliente': nuevo_cliente.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al registrar cliente: {str(e)}'}), 500


@app.route('/api/cliente/<int:id_cliente>', methods=['GET'])
def obtener_cliente(id_cliente):
    """
    Obtiene la información del perfil de un cliente.
    El cliente puede ver sus datos personales.
    """
    cliente = Cliente.query.get(id_cliente)
    
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    
    return jsonify(cliente.to_dict())


@app.route('/api/cliente/<int:id_cliente>', methods=['PUT'])
def actualizar_cliente(id_cliente):
    """
    Permite al cliente actualizar su información personal.
    """
    cliente = Cliente.query.get(id_cliente)
    
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    
    data = request.get_json()
    
    try:
        # Actualizar solo los campos proporcionados
        if 'nombre' in data:
            cliente.nombre = data['nombre']
        if 'apellido' in data:
            cliente.apellido = data['apellido']
        if 'telefono' in data:
            cliente.telefono = data['telefono']
        if 'email' in data:
            # Verificar que el email no esté en uso por otro cliente
            otro = Cliente.query.filter(Cliente.email == data['email'], Cliente.id_cliente != id_cliente).first()
            if otro:
                return jsonify({'error': 'El email ya está en uso'}), 409
            cliente.email = data['email']
        
        db.session.commit()
        return jsonify({
            'mensaje': 'Cliente actualizado exitosamente',
            'cliente': cliente.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar: {str(e)}'}), 500


# ==============================================================================
# LISTAR TODOS LOS CLIENTES (para formularios)
# ==============================================================================

@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    """
    Lista todos los clientes registrados.
    Útil para formularios de selección de cliente.
    """
    try:
        clientes = Cliente.query.all()
        return jsonify([cliente.to_dict() for cliente in clientes]), 200
    except Exception as e:
        return jsonify({'error': f'Error al listar clientes: {str(e)}'}), 500


# ==============================================================================
# CONSULTA DE CANCHAS DISPONIBLES
# ==============================================================================

@app.route('/api/canchas', methods=['GET'])
def listar_canchas():
    """
    Lista todas las canchas disponibles para reservar.
    El cliente puede ver qué canchas hay y sus características.
    
    Filtros opcionales:
    - tipo_deporte: filtra por tipo de deporte
    - activa: filtra solo canchas activas
    """
    tipo_deporte = request.args.get('tipo_deporte')
    solo_activas = request.args.get('activa', 'true').lower() == 'true'
    
    query = Cancha.query
    
    if solo_activas:
        query = query.filter_by(activa=True)
    
    if tipo_deporte:
        query = query.filter_by(tipo_deporte=tipo_deporte)
    
    canchas = query.all()
    
    # Devolver array directo para compatibilidad con el frontend
    return jsonify([c.to_dict() for c in canchas])


@app.route('/api/canchas/<int:id_cancha>', methods=['GET'])
def detalle_cancha(id_cancha):
    """
    Muestra detalles de una cancha específica.
    El cliente puede ver información detallada antes de reservar.
    """
    cancha = Cancha.query.get(id_cancha)
    
    if not cancha:
        return jsonify({'error': 'Cancha no encontrada'}), 404
    
    # Incluir horarios disponibles
    horarios = [h.to_dict() for h in cancha.horarios if h.disponible]
    
    return jsonify({
        'cancha': cancha.to_dict(),
        'horarios_disponibles': horarios
    })


@app.route('/api/canchas/<int:id_cancha>/disponibilidad', methods=['GET'])
def verificar_disponibilidad_cancha(id_cancha):
    """
    Verifica si una cancha está disponible en una fecha y hora específica.
    El cliente usa esto antes de intentar hacer una reserva.
    
    Query params requeridos:
    - fecha: formato YYYY-MM-DD
    - hora_inicio: formato HH:MM
    - hora_fin: formato HH:MM
    """
    cancha = Cancha.query.get(id_cancha)
    if not cancha or not cancha.activa:
        return jsonify({'error': 'Cancha no encontrada o inactiva'}), 404
    
    fecha_str = request.args.get('fecha')
    hora_inicio_str = request.args.get('hora_inicio')
    hora_fin_str = request.args.get('hora_fin')
    
    if not all([fecha_str, hora_inicio_str, hora_fin_str]):
        return jsonify({'error': 'Faltan parámetros: fecha, hora_inicio, hora_fin'}), 400
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Formato de fecha u hora inválido'}), 400
    
    # Validar horario
    valido, mensaje = validar_horario(fecha, hora_inicio, hora_fin)
    if not valido:
        return jsonify({'disponible': False, 'motivo': mensaje})
    
    # Verificar disponibilidad
    disponible, mensaje = verificar_disponibilidad(id_cancha, fecha, hora_inicio, hora_fin)
    
    return jsonify({
        'disponible': disponible,
        'motivo': mensaje,
        'cancha': cancha.to_dict()
    })


# ==============================================================================
# GESTIÓN DE RESERVAS (LO MÁS IMPORTANTE PARA EL CLIENTE)
# ==============================================================================

@app.route('/api/reservas/check', methods=['GET'])
def check_disponibilidad_reserva():
    """
    Verifica si una cancha está disponible para una fecha y horario específico.
    Query params: id_cancha, fecha_reserva, hora_inicio, hora_fin
    """
    try:
        id_cancha = request.args.get('id_cancha', type=int)
        fecha_str = request.args.get('fecha_reserva')
        hora_inicio_str = request.args.get('hora_inicio')
        hora_fin_str = request.args.get('hora_fin')
        
        if not all([id_cancha, fecha_str, hora_inicio_str, hora_fin_str]):
            return jsonify({'available': False, 'reason': 'Faltan parámetros requeridos'}), 400
        
        # Validar que la cancha existe
        cancha = Cancha.query.get(id_cancha)
        if not cancha or not cancha.activa:
            return jsonify({'available': False, 'reason': 'Cancha no encontrada o inactiva'}), 404
        
        # Parsear fecha y horas
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
        
        # Validar horario
        valido, mensaje = validar_horario(fecha, hora_inicio, hora_fin)
        if not valido:
            return jsonify({'available': False, 'reason': mensaje})
        
        # Verificar disponibilidad
        disponible, mensaje = verificar_disponibilidad(id_cancha, fecha, hora_inicio, hora_fin)
        
        return jsonify({
            'available': disponible,
            'reason': mensaje if not disponible else 'Disponible'
        })
    
    except ValueError as e:
        return jsonify({'available': False, 'reason': f'Formato de fecha/hora inválido: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'available': False, 'reason': f'Error al verificar disponibilidad: {str(e)}'}), 500


@app.route('/api/reservas', methods=['POST'])
def crear_reserva():
    """
    El cliente crea una nueva reserva de cancha.
    
    Body JSON esperado:
    {
        "id_cliente": 1,
        "id_cancha": 2,
        "fecha_reserva": "2024-11-15",
        "hora_inicio": "14:00",
        "hora_fin": "15:00",
        "servicios_adicionales": [1, 2]  // opcional
    }
    """
    data = request.get_json()
    
    # Validar campos requeridos
    campos_requeridos = ['id_cliente', 'id_cancha', 'fecha_reserva', 'hora_inicio', 'hora_fin']
    for campo in campos_requeridos:
        if campo not in data:
            return jsonify({'error': f'Falta el campo requerido: {campo}'}), 400
    
    # Validar que el cliente existe y está activo
    cliente = Cliente.query.get(data['id_cliente'])
    if not cliente or not cliente.activo:
        return jsonify({'error': 'Cliente no encontrado o inactivo'}), 404
    
    # Validar que la cancha existe y está activa
    cancha = Cancha.query.get(data['id_cancha'])
    if not cancha or not cancha.activa:
        return jsonify({'error': 'Cancha no encontrada o inactiva'}), 404
    
    # Parsear fecha y horas
    try:
        fecha_reserva = datetime.strptime(data['fecha_reserva'], '%Y-%m-%d').date()
        hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
        hora_fin = datetime.strptime(data['hora_fin'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Formato de fecha u hora inválido. Use YYYY-MM-DD para fecha y HH:MM para hora'}), 400
    
    # Validar horario
    valido, mensaje = validar_horario(fecha_reserva, hora_inicio, hora_fin)
    if not valido:
        return jsonify({'error': mensaje}), 400
    
    # Verificar disponibilidad
    disponible, mensaje = verificar_disponibilidad(data['id_cancha'], fecha_reserva, hora_inicio, hora_fin)
    if not disponible:
        return jsonify({'error': mensaje}), 409
    
    # Calcular precio
    servicios_ids = data.get('servicios_adicionales', [])
    precio_total = calcular_precio_reserva(data['id_cancha'], hora_inicio, hora_fin, servicios_ids)
    
    # Obtener estado "Pendiente" (o crear si no existe)
    estado_pendiente = EstadoReserva.query.filter_by(nombre='Pendiente').first()
    if not estado_pendiente:
        estado_pendiente = EstadoReserva(nombre='Pendiente')
        db.session.add(estado_pendiente)
        db.session.flush()
    
    try:
        # Crear la reserva
        nueva_reserva = Reserva(
            id_cliente=data['id_cliente'],
            id_cancha=data['id_cancha'],
            id_estado=estado_pendiente.id_estado,
            fecha_reserva=fecha_reserva,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            precio_total=precio_total
        )
        db.session.add(nueva_reserva)
        db.session.flush()  # Para obtener el id_reserva
        
        # Agregar servicios adicionales si se solicitaron
        for id_servicio in servicios_ids:
            servicio = ServicioAdicional.query.get(id_servicio)
            if servicio and servicio.activo:
                reserva_servicio = ReservaServicio(
                    id_reserva=nueva_reserva.id_reserva,
                    id_servicio=id_servicio,
                    cantidad=1
                )
                db.session.add(reserva_servicio)
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Reserva creada exitosamente',
            'reserva': nueva_reserva.to_dict(),
            'precio_total': str(precio_total)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear reserva: {str(e)}'}), 500


@app.route('/api/reservas', methods=['GET'])
def listar_reservas():
    """
    Lista reservas con filtros opcionales.
    Query params: id_cancha, fecha_reserva, id_cliente, estado
    """
    id_cancha = request.args.get('id_cancha', type=int)
    fecha_str = request.args.get('fecha_reserva')
    id_cliente = request.args.get('id_cliente', type=int)
    estado_nombre = request.args.get('estado')
    
    query = Reserva.query
    
    if id_cancha:
        query = query.filter_by(id_cancha=id_cancha)
    
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            query = query.filter_by(fecha_reserva=fecha)
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    
    if id_cliente:
        query = query.filter_by(id_cliente=id_cliente)
    
    if estado_nombre:
        estado = EstadoReserva.query.filter_by(nombre=estado_nombre).first()
        if estado:
            query = query.filter_by(id_estado=estado.id_estado)
    
    reservas = query.order_by(Reserva.fecha_reserva, Reserva.hora_inicio).all()
    
    return jsonify([r.to_dict() for r in reservas])


@app.route('/api/cliente/<int:id_cliente>/reservas', methods=['GET'])
def mis_reservas(id_cliente):
    """
    El cliente consulta todas sus reservas.
    Puede filtrar por estado usando query param ?estado=Confirmada
    """
    cliente = Cliente.query.get(id_cliente)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    
    estado_filtro = request.args.get('estado')
    
    query = Reserva.query.filter_by(id_cliente=id_cliente)
    
    if estado_filtro:
        estado = EstadoReserva.query.filter_by(nombre=estado_filtro).first()
        if estado:
            query = query.filter_by(id_estado=estado.id_estado)
    
    reservas = query.order_by(Reserva.fecha_reserva.desc(), Reserva.hora_inicio.desc()).all()
    
    return jsonify({
        'total': len(reservas),
        'reservas': [r.to_dict() for r in reservas]
    })


@app.route('/api/reservas/<int:id_reserva>', methods=['DELETE'])
def eliminar_reserva(id_reserva):
    """
    Elimina una reserva de la base de datos.
    Esto libera el horario para que pueda ser reservado nuevamente.
    """
    try:
        reserva = Reserva.query.get(id_reserva)
        
        if not reserva:
            return jsonify({'error': 'Reserva no encontrada'}), 404
        
        # Guardar información antes de eliminar para el mensaje de respuesta
        info_reserva = {
            'id_reserva': reserva.id_reserva,
            'cancha': reserva.cancha.nombre,
            'fecha': reserva.fecha_reserva.strftime('%Y-%m-%d'),
            'hora_inicio': reserva.hora_inicio.strftime('%H:%M'),
            'hora_fin': reserva.hora_fin.strftime('%H:%M')
        }
        
        # Eliminar servicios adicionales asociados (si los hay)
        ReservaServicio.query.filter_by(id_reserva=id_reserva).delete()
        
        # Eliminar pagos asociados (si los hay)
        Pago.query.filter_by(id_reserva=id_reserva).delete()
        
        # Eliminar la reserva
        db.session.delete(reserva)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Reserva eliminada exitosamente',
            'info': info_reserva
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar reserva: {str(e)}'}), 500


@app.route('/api/reservas/<int:id_reserva>', methods=['GET'])
def detalle_reserva(id_reserva):
    """
    Obtiene los detalles completos de una reserva específica.
    Incluye información de servicios adicionales y pagos.
    """
    reserva = Reserva.query.get(id_reserva)
    
    if not reserva:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    
    # Armar respuesta completa con servicios y pagos
    servicios = []
    for rs in reserva.servicios:
        servicios.append({
            'servicio': rs.servicio.to_dict(),
            'cantidad': rs.cantidad
        })
    
    pagos = [p.to_dict() for p in reserva.pagos]
    
    return jsonify({
        'reserva': reserva.to_dict(),
        'servicios_adicionales': servicios,
        'pagos': pagos
    })


@app.route('/api/reservas/<int:id_reserva>/cancelar', methods=['PUT'])
def cancelar_reserva(id_reserva):
    """
    El cliente puede cancelar su propia reserva.
    Solo se pueden cancelar reservas en estado 'Pendiente' o 'Confirmada'.
    """
    reserva = Reserva.query.get(id_reserva)
    
    if not reserva:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    
    # Verificar que la reserva pueda cancelarse
    if reserva.estado.nombre == 'Cancelada':
        return jsonify({'error': 'La reserva ya está cancelada'}), 400
    
    # Obtener o crear estado "Cancelada"
    estado_cancelada = EstadoReserva.query.filter_by(nombre='Cancelada').first()
    if not estado_cancelada:
        estado_cancelada = EstadoReserva(nombre='Cancelada')
        db.session.add(estado_cancelada)
        db.session.flush()
    
    try:
        reserva.id_estado = estado_cancelada.id_estado
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Reserva cancelada exitosamente',
            'reserva': reserva.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cancelar reserva: {str(e)}'}), 500


# ==============================================================================
# SERVICIOS ADICIONALES
# ==============================================================================

@app.route('/api/servicios', methods=['GET'])
def listar_servicios():
    """
    Lista todos los servicios adicionales disponibles.
    El cliente puede ver qué servicios puede contratar.
    """
    servicios = ServicioAdicional.query.filter_by(activo=True).all()
    
    return jsonify({
        'total': len(servicios),
        'servicios': [s.to_dict() for s in servicios]
    })


@app.route('/api/reservas/<int:id_reserva>/servicios', methods=['POST'])
def agregar_servicio_a_reserva(id_reserva):
    """
    Agrega un servicio adicional a una reserva existente.
    El cliente puede modificar su reserva agregando servicios.
    
    Body JSON:
    {
        "id_servicio": 1,
        "cantidad": 2
    }
    """
    reserva = Reserva.query.get(id_reserva)
    
    if not reserva:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    
    # Solo se pueden agregar servicios a reservas no canceladas
    if reserva.estado.nombre == 'Cancelada':
        return jsonify({'error': 'No se pueden agregar servicios a una reserva cancelada'}), 400
    
    data = request.get_json()
    
    if 'id_servicio' not in data:
        return jsonify({'error': 'Falta el campo id_servicio'}), 400
    
    servicio = ServicioAdicional.query.get(data['id_servicio'])
    if not servicio or not servicio.activo:
        return jsonify({'error': 'Servicio no encontrado o inactivo'}), 404
    
    cantidad = data.get('cantidad', 1)
    
    try:
        # Verificar si ya existe ese servicio en la reserva
        rs_existente = ReservaServicio.query.filter_by(
            id_reserva=id_reserva,
            id_servicio=data['id_servicio']
        ).first()
        
        if rs_existente:
            # Actualizar cantidad
            rs_existente.cantidad += cantidad
        else:
            # Crear nuevo
            nuevo_rs = ReservaServicio(
                id_reserva=id_reserva,
                id_servicio=data['id_servicio'],
                cantidad=cantidad
            )
            db.session.add(nuevo_rs)
        
        # Actualizar precio total de la reserva
        reserva.precio_total += Decimal(servicio.precio) * Decimal(cantidad)
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Servicio agregado exitosamente',
            'precio_total_actualizado': str(reserva.precio_total)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al agregar servicio: {str(e)}'}), 500


# ==============================================================================
# PAGOS
# ==============================================================================

@app.route('/api/metodos-pago', methods=['GET'])
def listar_metodos_pago():
    """
    Lista los métodos de pago disponibles.
    """
    metodos = MetodoPago.query.all()
    return jsonify({
        'metodos': [m.to_dict() for m in metodos]
    })


@app.route('/api/reservas/<int:id_reserva>/pago', methods=['POST'])
def registrar_pago(id_reserva):
    """
    El cliente registra un pago para su reserva.
    
    Body JSON:
    {
        "id_metodo": 1,
        "monto": 5000.00
    }
    """
    reserva = Reserva.query.get(id_reserva)
    
    if not reserva:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    
    if reserva.estado.nombre == 'Cancelada':
        return jsonify({'error': 'No se puede pagar una reserva cancelada'}), 400
    
    data = request.get_json()
    
    if 'id_metodo' not in data or 'monto' not in data:
        return jsonify({'error': 'Faltan campos requeridos: id_metodo, monto'}), 400
    
    metodo = MetodoPago.query.get(data['id_metodo'])
    if not metodo:
        return jsonify({'error': 'Método de pago no encontrado'}), 404
    
    try:
        nuevo_pago = Pago(
            id_reserva=id_reserva,
            id_metodo=data['id_metodo'],
            monto=Decimal(str(data['monto'])),
            estado='Aprobado'  # En un sistema real esto vendría de una pasarela de pago
        )
        db.session.add(nuevo_pago)
        
        # Si el pago cubre el total, marcar la reserva como Confirmada
        total_pagado = sum(Decimal(p.monto) for p in reserva.pagos) + Decimal(str(data['monto']))
        if total_pagado >= reserva.precio_total:
            estado_confirmada = EstadoReserva.query.filter_by(nombre='Confirmada').first()
            if estado_confirmada:
                reserva.id_estado = estado_confirmada.id_estado
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Pago registrado exitosamente',
            'pago': nuevo_pago.to_dict(),
            'estado_reserva': reserva.estado.nombre
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al registrar pago: {str(e)}'}), 500


@app.route('/api/cliente/<int:id_cliente>/pagos', methods=['GET'])
def historial_pagos(id_cliente):
    """
    Muestra el historial de pagos del cliente.
    """
    cliente = Cliente.query.get(id_cliente)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    
    # Obtener todos los pagos de las reservas del cliente
    pagos = db.session.query(Pago).join(Reserva).filter(
        Reserva.id_cliente == id_cliente
    ).order_by(Pago.fecha_pago.desc()).all()
    
    return jsonify({
        'total': len(pagos),
        'pagos': [p.to_dict() for p in pagos]
    })


# ==============================================================================
# REPORTES PARA EL CLIENTE
# ==============================================================================

@app.route('/api/cliente/<int:id_cliente>/estadisticas', methods=['GET'])
def estadisticas_cliente(id_cliente):
    """
    Muestra estadísticas del cliente:
    - Total de reservas realizadas
    - Total gastado
    - Canchas más reservadas
    - etc.
    """
    cliente = Cliente.query.get(id_cliente)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    
    # Total de reservas
    total_reservas = Reserva.query.filter_by(id_cliente=id_cliente).count()
    
    # Reservas confirmadas
    estado_confirmada = EstadoReserva.query.filter_by(nombre='Confirmada').first()
    reservas_confirmadas = 0
    if estado_confirmada:
        reservas_confirmadas = Reserva.query.filter_by(
            id_cliente=id_cliente,
            id_estado=estado_confirmada.id_estado
        ).count()
    
    # Total gastado (suma de pagos aprobados)
    pagos = db.session.query(Pago).join(Reserva).filter(
        Reserva.id_cliente == id_cliente,
        Pago.estado == 'Aprobado'
    ).all()
    total_gastado = sum(Decimal(p.monto) for p in pagos)
    
    # Cancha más reservada por el cliente
    from sqlalchemy import func
    cancha_favorita = db.session.query(
        Cancha.nombre,
        func.count(Reserva.id_reserva).label('veces')
    ).join(Reserva).filter(
        Reserva.id_cliente == id_cliente
    ).group_by(Cancha.id_cancha).order_by(func.count(Reserva.id_reserva).desc()).first()
    
    return jsonify({
        'cliente': cliente.to_dict(),
        'estadisticas': {
            'total_reservas': total_reservas,
            'reservas_confirmadas': reservas_confirmadas,
            'total_gastado': str(total_gastado),
            'cancha_favorita': {
                'nombre': cancha_favorita[0] if cancha_favorita else None,
                'veces_reservada': cancha_favorita[1] if cancha_favorita else 0
            }
        }
    })


# ==============================================================================
# INICIALIZACIÓN DE LA BASE DE DATOS
# ==============================================================================

def inicializar_datos_demo():
    """
    Crea datos de ejemplo para poder probar el sistema.
    Solo se ejecuta si la BD está vacía.
    """
    # Verificar si ya hay datos
    if Cliente.query.first():
        return
    
    print("Inicializando datos de demostración...")
    
    # Crear estados de reserva
    estados = ['Pendiente', 'Confirmada', 'Cancelada']
    for nombre in estados:
        estado = EstadoReserva(nombre=nombre)
        db.session.add(estado)
    
    # Crear métodos de pago
    metodos = ['Efectivo', 'Tarjeta de Débito', 'Tarjeta de Crédito', 'Transferencia', 'MercadoPago']
    for nombre in metodos:
        metodo = MetodoPago(nombre=nombre)
        db.session.add(metodo)
    
    # Crear canchas de ejemplo
    canchas_data = [
        # Canchas de Fútbol 5
        {'nombre': 'Cancha Fútbol 5 - Norte', 'tipo_deporte': 'Fútbol', 'superficie': 'Césped Sintético', 'precio_hora': 3500, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Fútbol 5 - Sur', 'tipo_deporte': 'Fútbol', 'superficie': 'Césped Sintético', 'precio_hora': 3500, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Fútbol 5 - Este', 'tipo_deporte': 'Fútbol', 'superficie': 'Césped Sintético', 'precio_hora': 3200, 'tiene_iluminacion': False},
        {'nombre': 'Cancha Fútbol 5 - Oeste Premium', 'tipo_deporte': 'Fútbol', 'superficie': 'Césped Sintético Premium', 'precio_hora': 4000, 'tiene_iluminacion': True},
        
        # Canchas de Fútbol 7 y 11
        {'nombre': 'Cancha Fútbol 7 - Principal', 'tipo_deporte': 'Fútbol', 'superficie': 'Césped Natural', 'precio_hora': 5000, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Fútbol 7 - Secundaria', 'tipo_deporte': 'Fútbol', 'superficie': 'Césped Sintético', 'precio_hora': 4500, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Fútbol 11', 'tipo_deporte': 'Fútbol', 'superficie': 'Césped Natural', 'precio_hora': 8000, 'tiene_iluminacion': True},
        
        # Canchas de Paddle
        {'nombre': 'Cancha Paddle 1 - Techada', 'tipo_deporte': 'Paddle', 'superficie': 'Césped Sintético', 'precio_hora': 2800, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Paddle 2 - Exterior', 'tipo_deporte': 'Paddle', 'superficie': 'Césped Sintético', 'precio_hora': 2500, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Paddle 3 - Premium', 'tipo_deporte': 'Paddle', 'superficie': 'Césped Sintético Premium', 'precio_hora': 3200, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Paddle 4 - Económica', 'tipo_deporte': 'Paddle', 'superficie': 'Césped Sintético', 'precio_hora': 2200, 'tiene_iluminacion': False},
        
        # Canchas de Tenis
        {'nombre': 'Cancha Tenis 1 - Polvo de Ladrillo', 'tipo_deporte': 'Tenis', 'superficie': 'Polvo de Ladrillo', 'precio_hora': 2000, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Tenis 2 - Cemento', 'tipo_deporte': 'Tenis', 'superficie': 'Cemento', 'precio_hora': 1800, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Tenis 3 - Césped', 'tipo_deporte': 'Tenis', 'superficie': 'Césped Natural', 'precio_hora': 2500, 'tiene_iluminacion': True},
        
        # Canchas de Básquet
        {'nombre': 'Cancha Básquet - Cubierta', 'tipo_deporte': 'Básquet', 'superficie': 'Parquet', 'precio_hora': 3000, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Básquet - Exterior', 'tipo_deporte': 'Básquet', 'superficie': 'Cemento', 'precio_hora': 2500, 'tiene_iluminacion': True},
        
        # Canchas de Vóley
        {'nombre': 'Cancha Vóley - Indoor', 'tipo_deporte': 'Vóley', 'superficie': 'Parquet', 'precio_hora': 2800, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Vóley - Playa', 'tipo_deporte': 'Vóley', 'superficie': 'Arena', 'precio_hora': 2200, 'tiene_iluminacion': False},
        
        # Otras opciones
        {'nombre': 'Cancha Hockey - Césped', 'tipo_deporte': 'Hockey', 'superficie': 'Césped Natural', 'precio_hora': 3500, 'tiene_iluminacion': True},
        {'nombre': 'Cancha Rugby', 'tipo_deporte': 'Rugby', 'superficie': 'Césped Natural', 'precio_hora': 7000, 'tiene_iluminacion': False},
    ]
    
    for c_data in canchas_data:
        cancha = Cancha(**c_data)
        db.session.add(cancha)
        db.session.flush()
        
        # Agregar horarios disponibles (Lunes a Domingo, 9:00 a 23:00)
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        for dia in dias:
            horario = HorarioDisponible(
                id_cancha=cancha.id_cancha,
                dia_semana=dia,
                hora_inicio=time(9, 0),
                hora_fin=time(23, 0),
                disponible=True
            )
            db.session.add(horario)
    
    # Crear servicios adicionales
    servicios_data = [
        {'nombre': 'Alquiler de Pelota', 'descripcion': 'Pelota de fútbol/paddle', 'precio': 500},
        {'nombre': 'Alquiler de Pecheras', 'descripcion': 'Set de 10 pecheras', 'precio': 300},
        {'nombre': 'Alquiler de Paletas', 'descripcion': 'Par de paletas de paddle', 'precio': 800},
        {'nombre': 'Servicio de Buffet', 'descripcion': 'Agua y snacks', 'precio': 1000},
        {'nombre': 'Estacionamiento', 'descripcion': 'Lugar de estacionamiento cubierto', 'precio': 200},
    ]
    
    for s_data in servicios_data:
        servicio = ServicioAdicional(**s_data)
        db.session.add(servicio)
    
    # Crear 10 clientes de ejemplo para pruebas
    clientes_data = [
        {'dni': '12345678', 'nombre': 'Juan', 'apellido': 'Pérez', 'telefono': '1134567890', 'email': 'juan.perez@example.com', 'activo': True},
        {'dni': '23456789', 'nombre': 'María', 'apellido': 'González', 'telefono': '1145678901', 'email': 'maria.gonzalez@example.com', 'activo': True},
        {'dni': '34567890', 'nombre': 'Carlos', 'apellido': 'Rodríguez', 'telefono': '1156789012', 'email': 'carlos.rodriguez@example.com', 'activo': True},
        {'dni': '44444444', 'nombre': 'Luis', 'apellido': 'Advincula', 'telefono': '1167890123', 'email': 'luis.advincula@example.com', 'activo': True},
        {'dni': '56789012', 'nombre': 'Ana', 'apellido': 'Martínez', 'telefono': '1178901234', 'email': 'ana.martinez@example.com', 'activo': True},
        {'dni': '67890123', 'nombre': 'Diego', 'apellido': 'López', 'telefono': '1189012345', 'email': 'diego.lopez@example.com', 'activo': True},
        {'dni': '78901234', 'nombre': 'Laura', 'apellido': 'Fernández', 'telefono': '1190123456', 'email': 'laura.fernandez@example.com', 'activo': True},
        {'dni': '89012345', 'nombre': 'Pablo', 'apellido': 'Sánchez', 'telefono': '1101234567', 'email': 'pablo.sanchez@example.com', 'activo': True},
        {'dni': '90123456', 'nombre': 'Sofía', 'apellido': 'Ramírez', 'telefono': '1112345678', 'email': 'sofia.ramirez@example.com', 'activo': True},
        {'dni': '11111111', 'nombre': 'Martín', 'apellido': 'Torres', 'telefono': '1123456789', 'email': 'martin.torres@example.com', 'activo': True},
    ]
    
    for c_data in clientes_data:
        cliente = Cliente(**c_data)
        db.session.add(cliente)
    
    db.session.commit()
    print("¡Datos de demostración creados exitosamente!")
    print(f"  - {len(clientes_data)} clientes")
    print(f"  - {len(canchas_data)} canchas")
    print(f"  - {len(servicios_data)} servicios adicionales")


# ==============================================================================
# MAIN - EJECUCIÓN DEL SERVIDOR
# ==============================================================================

if __name__ == '__main__':
    # Crear las tablas en la base de datos si no existen
    with app.app_context():
        db.create_all()
        inicializar_datos_demo()
    
    # Mensaje de inicio
    print("\n" + "="*70)
    print("  SISTEMA DE RESERVAS DE CANCHAS DEPORTIVAS - Perspectiva del Cliente")
    print("  Grupo G25 - Trabajo Práctico Integrador - DAO")
    print("="*70)
    print("\n📌 API corriendo en: http://localhost:5000")
    print("📚 Documentación Swagger: http://localhost:5000/api/docs")
    print("\n🎯 Endpoints principales para el CLIENTE:")
    print("  - POST /api/cliente/registro          → Registrarse en el sistema")
    print("  - GET  /api/canchas                   → Ver canchas disponibles")
    print("  - GET  /api/canchas/<id>/disponibilidad → Verificar disponibilidad")
    print("  - POST /api/reservas                  → Crear nueva reserva")
    print("  - GET  /api/cliente/<id>/reservas     → Ver mis reservas")
    print("  - PUT  /api/reservas/<id>/cancelar    → Cancelar reserva")
    print("  - GET  /api/servicios                 → Ver servicios adicionales")
    print("  - POST /api/reservas/<id>/pago        → Registrar pago")
    print("="*70 + "\n")
    
    # Iniciar el servidor Flask en modo debug
    app.run(debug=True, host='0.0.0.0', port=5000)
