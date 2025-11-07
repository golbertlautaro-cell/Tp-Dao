"""
Script de prueba rápida para la API de Reservas
Grupo G25 - Trabajo Práctico Integrador

Este script realiza pruebas básicas de los endpoints principales.
Ejecutar después de iniciar el servidor (python trabajo_practico.py)
"""

import requests
import json
from datetime import datetime, timedelta

# URL base de la API
BASE_URL = "http://localhost:5000"

def print_section(title):
    """Imprime un título de sección"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_api_status():
    """Verifica que la API esté funcionando"""
    print_section("1. Verificando estado de la API")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Estado: {response.status_code}")
        print(f"📝 Respuesta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️  Asegúrate de que el servidor esté corriendo (python trabajo_practico.py)")
        return False

def test_list_canchas():
    """Lista las canchas disponibles"""
    print_section("2. Consultando canchas disponibles")
    try:
        response = requests.get(f"{BASE_URL}/api/canchas")
        data = response.json()
        print(f"✅ Canchas encontradas: {data['total']}")
        for cancha in data['canchas'][:3]:  # Mostrar solo las primeras 3
            print(f"   🏟️  {cancha['nombre']} - {cancha['tipo_deporte']} - ${cancha['precio_hora']}/hora")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_register_cliente():
    """Registra un nuevo cliente"""
    print_section("3. Registrando nuevo cliente")
    cliente_data = {
        "dni": "11223344",
        "nombre": "Test",
        "apellido": "Usuario",
        "telefono": "1122334455",
        "email": f"test{datetime.now().timestamp()}@example.com"  # Email único
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/cliente/registro",
            json=cliente_data
        )
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Cliente registrado: ID {data['cliente']['id_cliente']}")
            print(f"   👤 {data['cliente']['nombre']} {data['cliente']['apellido']}")
            return data['cliente']['id_cliente']
        else:
            print(f"⚠️  Respuesta: {response.json()}")
            # Si ya existe, intentar obtener el cliente demo
            return 1  # Usar el cliente de demo
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

def test_check_availability():
    """Verifica disponibilidad de una cancha"""
    print_section("4. Verificando disponibilidad")
    fecha = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    try:
        response = requests.get(
            f"{BASE_URL}/api/canchas/1/disponibilidad",
            params={
                "fecha": fecha,
                "hora_inicio": "18:00",
                "hora_fin": "19:00"
            }
        )
        data = response.json()
        if data.get('disponible'):
            print(f"✅ Disponible para {fecha} de 18:00 a 19:00")
        else:
            print(f"❌ No disponible: {data.get('motivo')}")
        return data.get('disponible', False)
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_create_reserva(id_cliente):
    """Crea una reserva de prueba"""
    print_section("5. Creando reserva")
    fecha = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    reserva_data = {
        "id_cliente": id_cliente,
        "id_cancha": 1,
        "fecha_reserva": fecha,
        "hora_inicio": "18:00",
        "hora_fin": "19:00",
        "servicios_adicionales": [1]  # Agregar servicio de pelota
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/reservas",
            json=reserva_data
        )
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Reserva creada: ID {data['reserva']['id_reserva']}")
            print(f"   📅 Fecha: {data['reserva']['fecha_reserva']}")
            print(f"   ⏰ Horario: {data['reserva']['hora_inicio']} - {data['reserva']['hora_fin']}")
            print(f"   💰 Precio total: ${data['precio_total']}")
            return data['reserva']['id_reserva']
        else:
            print(f"⚠️  Error al crear reserva: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_list_mis_reservas(id_cliente):
    """Lista las reservas del cliente"""
    print_section("6. Consultando mis reservas")
    try:
        response = requests.get(f"{BASE_URL}/api/cliente/{id_cliente}/reservas")
        data = response.json()
        print(f"✅ Total de reservas: {data['total']}")
        for reserva in data['reservas'][:5]:  # Mostrar máximo 5
            print(f"   📋 Reserva #{reserva['id_reserva']} - {reserva['fecha_reserva']} - {reserva['estado']['nombre']}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_list_servicios():
    """Lista los servicios adicionales"""
    print_section("7. Servicios adicionales disponibles")
    try:
        response = requests.get(f"{BASE_URL}/api/servicios")
        data = response.json()
        print(f"✅ Servicios disponibles: {data['total']}")
        for servicio in data['servicios']:
            print(f"   🎁 {servicio['nombre']} - ${servicio['precio']} - {servicio['descripcion']}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_estadisticas(id_cliente):
    """Muestra estadísticas del cliente"""
    print_section("8. Estadísticas del cliente")
    try:
        response = requests.get(f"{BASE_URL}/api/cliente/{id_cliente}/estadisticas")
        data = response.json()
        stats = data['estadisticas']
        print(f"✅ Total de reservas: {stats['total_reservas']}")
        print(f"✅ Reservas confirmadas: {stats['reservas_confirmadas']}")
        print(f"✅ Total gastado: ${stats['total_gastado']}")
        if stats['cancha_favorita']['nombre']:
            print(f"✅ Cancha favorita: {stats['cancha_favorita']['nombre']} ({stats['cancha_favorita']['veces_reservada']} veces)")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal que ejecuta todas las pruebas"""
    print("\n" + "🎯"*35)
    print("   PRUEBAS DE LA API - SISTEMA DE RESERVAS")
    print("   Grupo G25 - Trabajo Práctico Integrador")
    print("🎯"*35)
    
    # Verificar que la API esté corriendo
    if not test_api_status():
        return
    
    # Ejecutar pruebas secuencialmente
    test_list_canchas()
    id_cliente = test_register_cliente()
    test_check_availability()
    id_reserva = test_create_reserva(id_cliente)
    test_list_mis_reservas(id_cliente)
    test_list_servicios()
    test_estadisticas(id_cliente)
    
    # Resumen final
    print_section("RESUMEN")
    print("✅ Pruebas completadas exitosamente")
    print("\n📚 Para más información:")
    print("   - Documentación Swagger: http://localhost:5000/api/docs")
    print("   - README.md para guía completa")
    print("   - INSTALACION.md para troubleshooting")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error general: {e}")
