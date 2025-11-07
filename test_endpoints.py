import requests
import json

BASE_URL = "http://localhost:5000"

print("=" * 60)
print("PRUEBA COMPLETA DE ENDPOINTS")
print("=" * 60)

# Test 1: Página principal
print("\n[1] GET / (Página principal)")
try:
    r = requests.get(f"{BASE_URL}/")
    print(f"✓ Status: {r.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: GET /api/clientes
print("\n[2] GET /api/clientes")
try:
    r = requests.get(f"{BASE_URL}/api/clientes")
    print(f"✓ Status: {r.status_code}")
    clientes = r.json()
    print(f"  Clientes encontrados: {len(clientes)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: GET /api/canchas
print("\n[3] GET /api/canchas")
try:
    r = requests.get(f"{BASE_URL}/api/canchas")
    print(f"✓ Status: {r.status_code}")
    canchas = r.json()
    print(f"  Canchas encontradas: {len(canchas)}")
    if len(canchas) > 0:
        print(f"  Primera cancha: {canchas[0]['nombre']}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: GET /api/servicios
print("\n[4] GET /api/servicios")
try:
    r = requests.get(f"{BASE_URL}/api/servicios")
    print(f"✓ Status: {r.status_code}")
    servicios = r.json()
    print(f"  Servicios encontrados: {len(servicios)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: GET /api/metodos-pago
print("\n[5] GET /api/metodos-pago")
try:
    r = requests.get(f"{BASE_URL}/api/metodos-pago")
    print(f"✓ Status: {r.status_code}")
    metodos = r.json()
    print(f"  Métodos de pago: {len(metodos)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 6: POST /api/cliente/registro
print("\n[6] POST /api/cliente/registro")
try:
    data = {
        "nombre": "Test",
        "apellido": "Usuario",
        "email": f"test{requests.get(f'{BASE_URL}/api/clientes').json().__len__()}@test.com",
        "telefono": "1234567890",
        "dni": f"9999{requests.get(f'{BASE_URL}/api/clientes').json().__len__()}"
    }
    r = requests.post(f"{BASE_URL}/api/cliente/registro", json=data)
    print(f"✓ Status: {r.status_code}")
    if r.status_code == 201:
        cliente = r.json()
        cliente_id = cliente['cliente']['id_cliente']
        print(f"  Cliente creado con ID: {cliente_id}")
        
        # Test 7: GET /api/cliente/<id>
        print(f"\n[7] GET /api/cliente/{cliente_id}")
        r2 = requests.get(f"{BASE_URL}/api/cliente/{cliente_id}")
        print(f"✓ Status: {r2.status_code}")
        
        # Test 8: GET /api/cliente/<id>/reservas
        print(f"\n[8] GET /api/cliente/{cliente_id}/reservas")
        r3 = requests.get(f"{BASE_URL}/api/cliente/{cliente_id}/reservas")
        print(f"✓ Status: {r3.status_code}")
        reservas = r3.json()
        print(f"  Reservas del cliente: {len(reservas)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 9: POST /api/reservas
print("\n[9] POST /api/reservas (crear reserva)")
try:
    # Obtener primer cliente y primera cancha
    clientes = requests.get(f"{BASE_URL}/api/clientes").json()
    canchas = requests.get(f"{BASE_URL}/api/canchas").json()
    
    if len(clientes) > 0 and len(canchas) > 0:
        data = {
            "id_cliente": clientes[0]['id_cliente'],
            "id_cancha": canchas[0]['id_cancha'],
            "fecha_reserva": "2025-11-15",
            "hora_inicio": "14:00",
            "hora_fin": "15:00"
        }
        r = requests.post(f"{BASE_URL}/api/reservas", json=data)
        print(f"✓ Status: {r.status_code}")
        if r.status_code == 201:
            reserva = r.json()
            reserva_id = reserva['reserva']['id_reserva']
            print(f"  Reserva creada con ID: {reserva_id}")
            
            # Test 10: GET /api/reservas/<id>
            print(f"\n[10] GET /api/reservas/{reserva_id}")
            r2 = requests.get(f"{BASE_URL}/api/reservas/{reserva_id}")
            print(f"✓ Status: {r2.status_code}")
    else:
        print("✗ No hay clientes o canchas para crear reserva")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 11: Páginas UI
print("\n[11] Páginas UI")
paginas = ["/ui/registro", "/ui/canchas", "/ui/reservar", "/ui/mis-reservas", "/ui/perfil"]
for pagina in paginas:
    try:
        r = requests.get(f"{BASE_URL}{pagina}")
        print(f"✓ {pagina}: {r.status_code}")
    except Exception as e:
        print(f"✗ {pagina}: Error")

print("\n" + "=" * 60)
print("PRUEBAS COMPLETADAS")
print("=" * 60)
