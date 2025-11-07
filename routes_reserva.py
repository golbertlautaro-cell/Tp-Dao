from flask import Blueprint, request, jsonify
from app import db
from models import (
    Reserva,
    Cliente,
    Cancha,
    HorarioDisponible,
    EstadoReserva,
    ServicioAdicional,
    ReservaServicio,
    Pago,
    Partido,
)
from datetime import datetime, date as _date
from decimal import Decimal

bp = Blueprint('reservas', __name__)


def time_from_str(s: str):
    return datetime.strptime(s, '%H:%M').time()


def date_from_str(s: str):
    return datetime.strptime(s, '%Y-%m-%d').date()


@bp.route('/', methods=['POST'])
def create_reserva():
    data = request.get_json() or {}
    try:
        id_cliente = int(data.get('id_cliente'))
        id_cancha = int(data.get('id_cancha'))
        fecha_reserva = date_from_str(data.get('fecha_reserva'))
        hora_inicio = time_from_str(data.get('hora_inicio'))
        hora_fin = time_from_str(data.get('hora_fin'))
    except Exception:
        return jsonify({'error': 'Campos inválidos o formato incorrecto. fecha: YYYY-MM-DD, horas: HH:MM'}), 400

    if hora_inicio >= hora_fin:
        return jsonify({'error': 'hora_inicio debe ser anterior a hora_fin'}), 400

    # Validar que las horas sean "en punto" y la duración sea un número entero de horas
    dt_start = datetime.combine(fecha_reserva, hora_inicio)
    dt_end = datetime.combine(fecha_reserva, hora_fin)
    # minutos deben ser 0
    if hora_inicio.minute != 0 or hora_fin.minute != 0:
        return jsonify({'error': 'Las horas deben ser en punto (ej. 07:00, 08:00). No se permiten minutos distintos de 00.'}), 400
    # rango permitido: 09:00 - 23:00 (hora inicio >= 9, hora fin <= 23)
    if hora_inicio.hour < 9 or hora_fin.hour > 23:
        return jsonify({'error': 'Horario fuera de rango. Las reservas sólo pueden realizarse entre 09:00 y 23:00.'}), 400
    # La fecha de reserva no puede ser anterior al día de hoy
    if fecha_reserva < _date.today():
        return jsonify({'error': 'La fecha de la reserva no puede ser anterior a la fecha actual.'}), 400
    # duración EXACTA de 1 hora
    if (dt_end - dt_start).total_seconds() != 3600:
        return jsonify({'error': 'La reserva debe tener una duración EXACTA de 1 hora (ej. 09:00-10:00).'}), 400

    # Verificar existencia de cliente y cancha
    cliente = Cliente.query.get(id_cliente)
    if not cliente or not cliente.activo:
        return jsonify({'error': 'Cliente no existe o no está activo'}), 400

    cancha = Cancha.query.get(id_cancha)
    if not cancha or not cancha.activa:
        return jsonify({'error': 'Cancha no existe o no está activa'}), 400

    # Validar que exista un estado por defecto (Pendiente) para asignar
    estado_default = EstadoReserva.query.filter_by(nombre='Pendiente').first() or EstadoReserva.query.first()
    if not estado_default:
        return jsonify({'error': 'No hay estados de reserva definidos. Cree al menos uno (ej: Pendiente)'}), 400

    # Si hay horarios definidos para la cancha, validar que el horario solicitado esté contenido
    horarios = HorarioDisponible.query.filter_by(id_cancha=id_cancha).all()
    if horarios:
        # Determinar nombre del día en español para comparar con dia_semana si así se usa
        weekday_es = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'][fecha_reserva.weekday()]
        ok = False
        for h in horarios:
            if h.dia_semana and h.dia_semana.lower() != weekday_es.lower():
                continue
            # si el horario cubre el intervalo solicitado
            if (h.hora_inicio <= hora_inicio) and (h.hora_fin >= hora_fin) and h.disponible:
                ok = True
                break
        if not ok:
            return jsonify({'error': 'HORARIO_DISPONIBLE: La cancha no tiene un horario disponible que cubra el intervalo solicitado'}), 409

    # Verificar solapamientos con otras reservas en la misma cancha y fecha
    overlapping = Reserva.query.filter(
        Reserva.id_cancha == id_cancha,
        Reserva.fecha_reserva == fecha_reserva,
        # no (existing.hora_fin <= inicio or existing.hora_inicio >= fin)
        Reserva.hora_fin > hora_inicio,
        Reserva.hora_inicio < hora_fin,
    ).first()
    if overlapping:
        return jsonify({'error': 'RESERVAS: Ya existe una reserva en ese horario para la cancha seleccionada'}), 409

    # Verificar solapamientos con PARTIDOS en la misma cancha y fecha
    partido_overlap = Partido.query.filter(
        Partido.id_cancha == id_cancha,
        Partido.fecha_partido == fecha_reserva,
        Partido.hora_fin > hora_inicio,
        Partido.hora_inicio < hora_fin,
    ).first()
    if partido_overlap:
        return jsonify({'error': 'PARTIDOS: Ya existe un partido en ese horario para la cancha seleccionada'}), 409

    # Calcular precio: precio_hora * duración + servicios + iluminación si aplica
    # duración en horas (decimal)
    duration_hours = Decimal((dt_end - dt_start).total_seconds() / 3600)
    precio_base = Decimal(cancha.precio_hora or Decimal('0'))
    total = (precio_base * duration_hours)

    # Iluminación: opción removida del UI — siempre False en backend por compatibilidad
    usa_iluminacion = False

    # Crear la reserva con estado por defecto
    reserva = Reserva(
        id_cliente=id_cliente,
        id_cancha=id_cancha,
        id_estado=estado_default.id_estado,
        fecha_reserva=fecha_reserva,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        precio_total=total.quantize(Decimal('0.01')),
        usa_iluminacion=usa_iluminacion,
    )
    db.session.add(reserva)
    db.session.flush()  # obtener id_reserva sin commit todavía

    # Procesar servicios adicionales (lista de objetos con id_servicio y cantidad opcional)
    servicios = data.get('servicios_adicionales') or []
    for s in servicios:
        # soportamos dos formatos:
        # - id numérico (referencia a ServicioAdicional existente)
        # - objeto { nombre: str, precio: number, cantidad: int } — creamos o buscamos el servicio y lo asociamos
        if isinstance(s, dict):
            cantidad = int(s.get('cantidad', 1))
            sid = s.get('id_servicio')
            if sid:
                svc = ServicioAdicional.query.get(sid)
                if not svc or not svc.activo:
                    db.session.rollback()
                    return jsonify({'error': f'Servicio adicional inválido: {sid}'}), 400
            else:
                # servicio dinámico enviado desde el frontend: buscar por nombre (case-insensitive) o crear uno nuevo
                nombre = (s.get('nombre') or '').strip()
                if not nombre:
                    db.session.rollback()
                    return jsonify({'error': 'Servicio adicional con nombre vacío'}), 400
                precio_raw = s.get('precio')
                try:
                    precio_decimal = Decimal(str(precio_raw)) if precio_raw is not None else Decimal('0')
                except Exception:
                    db.session.rollback()
                    return jsonify({'error': f'Precio inválido para servicio {nombre}'}), 400

                svc = ServicioAdicional.query.filter(ServicioAdicional.nombre.ilike(nombre)).first()
                if not svc:
                    svc = ServicioAdicional(nombre=nombre, precio_adicional=precio_decimal, activo=True)
                    db.session.add(svc)
                    db.session.flush()  # obtener id_servicio
                # Note: si existe svc con distinto precio, usamos el precio registrado en la tabla para facturación
        else:
            # valor simple: id de servicio
            cantidad = 1
            try:
                sid = int(s)
            except Exception:
                db.session.rollback()
                return jsonify({'error': f'Servicio adicional inválido: {s}'}), 400
            svc = ServicioAdicional.query.get(sid)
            if not svc or not svc.activo:
                db.session.rollback()
                return jsonify({'error': f'Servicio adicional inválido: {sid}'}), 400

        # asociar servicio a la reserva
        rs = ReservaServicio(id_reserva=reserva.id_reserva, id_servicio=svc.id_servicio, cantidad=cantidad)
        db.session.add(rs)
        # sumar precio usando el precio guardado en la tabla (o el creado recientemente)
        total += (Decimal(svc.precio_adicional) * Decimal(cantidad))

    reserva.precio_total = total.quantize(Decimal('0.01'))

    # Commit final
    db.session.commit()

    return jsonify({'id_reserva': reserva.id_reserva, 'precio_total': str(reserva.precio_total)}), 201


@bp.route('/', methods=['GET'])
def list_reservas():
    """Listar reservas. Query params opcionales: id_cancha, fecha_reserva=YYYY-MM-DD"""
    try:
        id_cancha = request.args.get('id_cancha')
        fecha_str = request.args.get('fecha_reserva')
        q = Reserva.query
        if id_cancha:
            q = q.filter(Reserva.id_cancha == int(id_cancha))
        if fecha_str:
            fecha = date_from_str(fecha_str)
            q = q.filter(Reserva.fecha_reserva == fecha)
    except Exception:
        return jsonify({'error': 'Parámetros inválidos'}), 400

    reservas = q.all()
    out = []
    for r in reservas:
        out.append({
            'id_reserva': r.id_reserva,
            'id_cliente': r.id_cliente,
            'cliente_nombre': getattr(r.cliente, 'nombre', None),
            'cliente_apellido': getattr(r.cliente, 'apellido', None),
            'id_cancha': r.id_cancha,
            'fecha_reserva': r.fecha_reserva.isoformat(),
            'hora_inicio': r.hora_inicio.strftime('%H:%M'),
            'hora_fin': r.hora_fin.strftime('%H:%M'),
            'precio_total': str(r.precio_total),
            'usa_iluminacion': bool(r.usa_iluminacion),
        })
    return jsonify(out)


@bp.route('/<int:id_reserva>', methods=['GET'])
def get_reserva(id_reserva):
    r = Reserva.query.get_or_404(id_reserva)
    return jsonify({
        'id_reserva': r.id_reserva,
        'id_cliente': r.id_cliente,
        'cliente_nombre': getattr(r.cliente, 'nombre', None),
        'cliente_apellido': getattr(r.cliente, 'apellido', None),
        'id_cancha': r.id_cancha,
        'fecha_reserva': r.fecha_reserva.isoformat(),
        'hora_inicio': r.hora_inicio.strftime('%H:%M'),
        'hora_fin': r.hora_fin.strftime('%H:%M'),
        'precio_total': str(r.precio_total),
        'usa_iluminacion': bool(r.usa_iluminacion),
    })


@bp.route('/check', methods=['GET'])
def check_disponibilidad():
    """Verifica si un intervalo en una cancha y fecha está disponible.

    Query params esperados: id_cancha, fecha_reserva (YYYY-MM-DD), hora_inicio (HH:MM), hora_fin (HH:MM)
    Retorna JSON { available: True } o { available: False, reason: '...' }
    """
    try:
        id_cancha = int(request.args.get('id_cancha'))
        fecha_reserva = date_from_str(request.args.get('fecha_reserva'))
        hora_inicio = time_from_str(request.args.get('hora_inicio'))
        hora_fin = time_from_str(request.args.get('hora_fin'))
    except Exception:
        return jsonify({'error': 'Parámetros inválidos. id_cancha int, fecha: YYYY-MM-DD, horas: HH:MM'}), 400

    if hora_inicio >= hora_fin:
        return jsonify({'available': False, 'reason': 'hora_inicio_mayor_o_igual_hora_fin'}), 200

    # Validar que las horas sean en punto y duración EXACTA de 1 hora
    if hora_inicio.minute != 0 or hora_fin.minute != 0:
        return jsonify({'available': False, 'reason': 'HORAS_DEBEN_SER_EN_PUNTO'}), 200
    dt_start = datetime.combine(fecha_reserva, hora_inicio)
    dt_end = datetime.combine(fecha_reserva, hora_fin)
    if (dt_end - dt_start).total_seconds() != 3600:
        return jsonify({'available': False, 'reason': 'DURACION_DEBE_SER_1_HORA'}), 200

    # rango permitido de inicio: 09:00 - 22:00 (hora_fin máxima 23:00)
    if hora_inicio.hour < 9 or hora_inicio.hour > 22 or hora_fin.hour > 23:
        return jsonify({'available': False, 'reason': 'HORARIO_FUERA_RANGO_09_22_START'}), 200

    cancha = Cancha.query.get(id_cancha)
    if not cancha or not cancha.activa:
        return jsonify({'available': False, 'reason': 'cancha_no_existente_o_inactiva'}), 200

    # Si hay horarios definidos para la cancha, validar que el horario solicitado esté contenido
    horarios = HorarioDisponible.query.filter_by(id_cancha=id_cancha).all()
    if horarios:
        weekday_es = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'][fecha_reserva.weekday()]
        ok = False
        for h in horarios:
            if h.dia_semana and h.dia_semana.lower() != weekday_es.lower():
                continue
            if (h.hora_inicio <= hora_inicio) and (h.hora_fin >= hora_fin) and h.disponible:
                ok = True
                break
        if not ok:
            return jsonify({'available': False, 'reason': 'HORARIO_DISPONIBLE: La cancha no tiene un horario que cubra el intervalo solicitado'}), 200

    # Verificar solapamientos con otras reservas
    overlapping = Reserva.query.filter(
        Reserva.id_cancha == id_cancha,
        Reserva.fecha_reserva == fecha_reserva,
        Reserva.hora_fin > hora_inicio,
        Reserva.hora_inicio < hora_fin,
    ).first()
    if overlapping:
        return jsonify({'available': False, 'reason': 'RESERVAS: Ya existe una reserva en ese horario para la cancha seleccionada'}), 200

    # Verificar solapamientos con PARTIDOS
    partido_overlap = Partido.query.filter(
        Partido.id_cancha == id_cancha,
        Partido.fecha_partido == fecha_reserva,
        Partido.hora_fin > hora_inicio,
        Partido.hora_inicio < hora_fin,
    ).first()
    if partido_overlap:
        return jsonify({'available': False, 'reason': 'PARTIDOS: Ya existe un partido en ese horario para la cancha seleccionada'}), 200

    return jsonify({'available': True}), 200


@bp.route('/<int:id_reserva>', methods=['PUT'])
def update_reserva(id_reserva):
    reserva = Reserva.query.get_or_404(id_reserva)
    data = request.get_json() or {}
    try:
        # permitir cambiar cliente, cancha, fecha y horas (mismo formato que create)
        id_cliente = int(data.get('id_cliente', reserva.id_cliente))
        id_cancha = int(data.get('id_cancha', reserva.id_cancha))
        fecha_reserva = date_from_str(data.get('fecha_reserva')) if data.get('fecha_reserva') else reserva.fecha_reserva
        hora_inicio = time_from_str(data.get('hora_inicio')) if data.get('hora_inicio') else reserva.hora_inicio
        hora_fin = time_from_str(data.get('hora_fin')) if data.get('hora_fin') else reserva.hora_fin
    except Exception:
        return jsonify({'error': 'Campos inválidos o formato incorrecto. fecha: YYYY-MM-DD, horas: HH:MM'}), 400

    if hora_inicio >= hora_fin:
        return jsonify({'error': 'hora_inicio debe ser anterior a hora_fin'}), 400

    # Validaciones: en punto, duración 1h, rango 09-23 (inicio 09-22)
    if hora_inicio.minute != 0 or hora_fin.minute != 0:
        return jsonify({'error': 'Las horas deben ser en punto (MM=00)'}), 400
    dt_start = datetime.combine(fecha_reserva, hora_inicio)
    dt_end = datetime.combine(fecha_reserva, hora_fin)
    if (dt_end - dt_start).total_seconds() != 3600:
        return jsonify({'error': 'La reserva debe durar exactamente 1 hora'}), 400
    if hora_inicio.hour < 9 or hora_inicio.hour > 22 or hora_fin.hour > 23:
        return jsonify({'error': 'Horario fuera del rango permitido (inicio 09-22, fin <=23)'}), 400

    # No permitir mover/crear una reserva a una fecha pasada
    if fecha_reserva < _date.today():
        return jsonify({'error': 'La fecha de la reserva no puede ser anterior a la fecha actual.'}), 400

    # verificar cliente y cancha
    cliente = Cliente.query.get(id_cliente)
    if not cliente or not cliente.activo:
        return jsonify({'error': 'Cliente no existe o no está activo'}), 400
    cancha = Cancha.query.get(id_cancha)
    if not cancha or not cancha.activa:
        return jsonify({'error': 'Cancha no existe o no está activa'}), 400

    # verificar horarios definidos para cancha
    horarios = HorarioDisponible.query.filter_by(id_cancha=id_cancha).all()
    if horarios:
        weekday_es = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'][fecha_reserva.weekday()]
        ok = False
        for h in horarios:
            if h.dia_semana and h.dia_semana.lower() != weekday_es.lower():
                continue
            if (h.hora_inicio <= hora_inicio) and (h.hora_fin >= hora_fin) and h.disponible:
                ok = True
                break
        if not ok:
            return jsonify({'error': 'La cancha no tiene un horario disponible que cubra el intervalo solicitado'}), 409

    # verificar solapamientos con otras reservas (excluir la actual)
    overlapping = Reserva.query.filter(
        Reserva.id_cancha == id_cancha,
        Reserva.fecha_reserva == fecha_reserva,
        Reserva.hora_fin > hora_inicio,
        Reserva.hora_inicio < hora_fin,
        Reserva.id_reserva != id_reserva,
    ).first()
    if overlapping:
        return jsonify({'error': 'Ya existe una reserva en ese horario para la cancha seleccionada'}), 409

    # verificar solapamientos con partidos
    partido_overlap = Partido.query.filter(
        Partido.id_cancha == id_cancha,
        Partido.fecha_partido == fecha_reserva,
        Partido.hora_fin > hora_inicio,
        Partido.hora_inicio < hora_fin,
    ).first()
    if partido_overlap:
        return jsonify({'error': 'Ya existe un partido en ese horario para la cancha seleccionada'}), 409

    # aplicar cambios
    reserva.id_cliente = id_cliente
    reserva.id_cancha = id_cancha
    reserva.fecha_reserva = fecha_reserva
    reserva.hora_inicio = hora_inicio
    reserva.hora_fin = hora_fin
    # Iluminación removida de UI: no se acepta/actualiza desde el payload

    db.session.commit()
    return jsonify({'message': 'Reserva actualizada', 'id_reserva': reserva.id_reserva})


@bp.route('/<int:id_reserva>', methods=['DELETE'])
def delete_reserva(id_reserva):
    reserva = Reserva.query.get_or_404(id_reserva)
    try:
        # eliminar servicios y pagos asociados
        ReservaServicio.query.filter_by(id_reserva=id_reserva).delete()
        Pago.query.filter_by(id_reserva=id_reserva).delete()
        db.session.delete(reserva)
        db.session.commit()
        return jsonify({'message': 'Reserva eliminada'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al eliminar reserva', 'details': str(e)}), 500
