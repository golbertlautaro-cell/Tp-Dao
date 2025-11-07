import sqlite3

conn = sqlite3.connect('c:/Users/usuario/Desktop/tpDao/reservas_cliente.db')
cursor = conn.cursor()

cursor.execute('SELECT id_reserva, id_cliente, id_cancha, fecha_reserva, hora_inicio, hora_fin, precio_total FROM reserva')
reservas = cursor.fetchall()

print('\n📋 RESERVAS EN LA BASE DE DATOS:\n')
if reservas:
    for r in reservas:
        print(f'ID: {r[0]} | Cliente ID: {r[1]} | Cancha ID: {r[2]} | Fecha: {r[3]} | {r[4]} - {r[5]} | Precio: ${r[6]}')
    print(f'\n✅ Total: {len(reservas)} reservas')
else:
    print('❌ No hay reservas en la tabla')

conn.close()
