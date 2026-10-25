"""
Genera un año de datos simulados con el modelo de la app Patitas amigas (src/data/types.ts).

Mismas reglas que la app: agenda de lunes a viernes, de 9 a 12:30 y de 16 a 19, de a 30 minutos;
cada motivo ocupa lo que dura; seña de $5.000 al pedir el turno desde la app; precios de la tienda
y de cada motivo iguales a los de la app. La semilla aleatoria es fija: siempre sale lo mismo.

Uso: python scripts/generar_datos.py   (escribe datos/crudos/*.csv)
"""
from datetime import date, timedelta
from pathlib import Path
import csv
import random

R = random.Random(2026)
DESDE, HASTA = date(2025, 10, 1), date(2026, 9, 30)  # el año que mira el tablero
HOY = HASTA  # "hoy" del tablero: lo posterior son turnos pedidos que todavía no pasaron
FIN_AGENDA = HOY + timedelta(days=21)
SALIDA = Path(__file__).resolve().parent.parent / 'datos' / 'crudos'

# ---- Lo mismo que la app (src/lib/agenda.ts, seed.ts, Atender.tsx) ----
def rango(desde, hasta):
    a, b = [int(x[:2]) * 60 + int(x[3:]) for x in (desde, hasta)]
    return [f'{m // 60:02d}:{m % 60:02d}' for m in range(a, b, 30)]

MANIANA, TARDE = rango('09:00', '12:30'), rango('16:00', '19:00')
HORARIOS = MANIANA + TARDE
DURACION = {'Control': 30, 'Vacuna': 30, 'Consulta': 60, 'Cirugía': 120}
PRECIO = {'Control': 15000, 'Vacuna': 12000, 'Consulta': 18000, 'Cirugía': 120000}
SENA = 5000
MEDIOS = ['Efectivo', 'Débito', 'Crédito', 'Transferencia', 'Mercado Pago']
VETERINARIOS = [
    {'id': 7, 'nombre': 'Dra. Paz Ruiz', 'especialidad': 'Clínica general', 'rol': 'veterinario'},
    {'id': 8, 'nombre': 'Dr. Tomás Vera', 'especialidad': 'Dermatología', 'rol': 'veterinario'},
    {'id': 9, 'nombre': 'Ana Sosa', 'especialidad': 'Recepción', 'rol': 'recepcion'},
]
PRODUCTOS = [
    {'id': 101, 'nombre': 'Alimento balanceado adulto 3 kg', 'precio': 18900, 'stock': 12, 'minimo': 6, 'duraDias': 30},
    {'id': 102, 'nombre': 'Pipeta antipulgas perro mediano', 'precio': 9500, 'stock': 30, 'minimo': 10, 'duraDias': 30},
    {'id': 103, 'nombre': 'Collar antiparasitario', 'precio': 14200, 'stock': 8, 'minimo': 10, 'duraDias': 180},
    {'id': 104, 'nombre': 'Shampoo neutro 250 ml', 'precio': 6300, 'stock': 15, 'minimo': 5, 'duraDias': ''},
    {'id': 105, 'nombre': 'Arena sanitaria 4 kg', 'precio': 7800, 'stock': 0, 'minimo': 5, 'duraDias': 20},
]
VACUNAS = {'perro': ['Antirrábica', 'Séxtuple', 'Tos de las perreras'], 'gato': ['Antirrábica', 'Triple felina', 'Leucemia felina']}
RAZAS = {'perro': ['Mestiza', 'Caniche', 'Labrador', 'Beagle', 'Golden', 'Bulldog francés', 'Ovejero alemán'], 'gato': ['Europeo común', 'Siamés', 'Mestiza', 'Persa']}

NOMBRES = 'Marta Julián Sofía Carlos Lucía Ramiro Ana Pablo Valeria Diego Florencia Martín Carolina Nicolás Paula Federico Laura Gustavo Romina Matías Agustina Hernán Silvina Joaquín Cecilia Emiliano Daniela Sebastián Mariela Facundo Gabriela Leandro Natalia Ignacio Verónica Tomás Belén Esteban Jimena Mauro'.split()
APELLIDOS = 'Gómez Pereyra Álvarez Benítez Ferreyra Ortiz Fernández López Martínez Rodríguez Sosa Díaz Romero Torres Ruiz Acosta Medina Herrera Suárez Aguirre Castro Molina Rojas Navarro Domínguez Vega Ríos Cabrera Paz Godoy'.split()
MASCOTAS = 'Luna Michi Toby Nala Rocco Coco Mora Simba Lola Milo Kira Thor Frida Olivia Bruno Maya Tango Pancho Uma Chispa Felipe Mía Lupe Oreo Canela Nino Pelusa Zeus Lía Ramón'.split()

dias = [DESDE + timedelta(n) for n in range((FIN_AGENDA - DESDE).days + 1)]
habiles = [d for d in dias if d.weekday() < 5]


def mas(hora, minutos):
    m = int(hora[:2]) * 60 + int(hora[3:]) + minutos
    return f'{m // 60:02d}:{m % 60:02d}'


def bloques(hora, motivo):
    """Bloques de 30 que ocupa un turno; None si no entra seguido (como bloquesDe en la app)."""
    n, i = DURACION[motivo] // 30, HORARIOS.index(hora)
    out = HORARIOS[i:i + n]
    return out if len(out) == n and mas(hora, (n - 1) * 30) == out[-1] else None


# ---- Clientes y mascotas ----
clientes, mascotas = [], []
for i in range(350):
    cid = 1024 + i
    clientes.append({'id': cid, 'nombre': f'{R.choice(NOMBRES)} {R.choice(APELLIDOS)}', 'dni': str(R.randint(20_000_000, 45_000_000)),
                     'telefono': f'249 4{R.randint(10, 79)}-{R.randint(1000, 9999)}', 'whatsapp': R.random() < 0.75})
    for _ in range(R.choices([1, 2, 3], [70, 24, 6])[0]):
        esp = 'perro' if R.random() < 0.62 else 'gato'
        mascotas.append({'id': len(mascotas) + 1, 'clienteId': cid, 'nombre': R.choice(MASCOTAS), 'especie': esp, 'edad': R.randint(0, 14),
                         'raza': R.choice(RAZAS[esp]), 'peso': round(R.uniform(3, 34) if esp == 'perro' else R.uniform(2.5, 6.5), 1)})

# Vacunas aplicadas antes del período: su próxima dosis cae dentro del año.
vacunas = []
ultima = {}  # (mascotaId, vacuna) -> última aplicación


def aplicar(mid, nombre, fecha):
    v = {'mascotaId': mid, 'nombre': nombre, 'aplicada': fecha, 'proxima': fecha + timedelta(365)}
    vacunas.append(v)
    ultima[(mid, nombre)] = v


for m in mascotas:
    for v in VACUNAS[m['especie']]:
        if R.random() < 0.5:
            aplicar(m['id'], v, DESDE - timedelta(R.randint(1, 365)))


# ---- Agenda ----
# Ocupación: más a la mañana, los lunes y en primavera (temporada de vacunas y pulgas).
DEMANDA_DIA = [0.72, 0.62, 0.6, 0.6, 0.52]
DEMANDA_MES = {1: 0.6, 2: 0.65, 3: 0.85, 4: 0.85, 5: 0.75, 6: 0.65, 7: 0.7, 8: 0.8, 9: 0.95, 10: 1.0, 11: 0.95, 12: 0.75}
turnos, esperas, movimientos = [], [], []


def mov(fecha, hora, tipo, concepto, monto, medio, por):
    movimientos.append({'id': len(movimientos) + 1, 'fecha': fecha, 'hora': hora, 'tipo': tipo, 'concepto': concepto, 'monto': monto, 'medio': medio, 'por': por})


citadas = set()  # vacunas que ya tienen turno


def mascota_para(motivo, fecha):
    """Para vacunar, casi siempre alguien a quien le toca (o ya se le pasó). El resto, cualquiera."""
    if motivo != 'Vacuna':
        return R.choice(mascotas)['id']
    vencen = [k for k, v in ultima.items() if v['proxima'] <= fecha + timedelta(20) and (k, v['aplicada']) not in citadas]
    if vencen and R.random() < 0.85:
        mid, nombre = R.choice(vencen)
    else:
        m = R.choice(mascotas)
        mid, nombre = m['id'], R.choice(VACUNAS[m['especie']])
    citadas.add(((mid, nombre), ultima[(mid, nombre)]['aplicada'] if (mid, nombre) in ultima else None))
    if fecha <= HOY:  # turno ya pasado: se aplicó ese día
        aplicar(mid, nombre, fecha)
    return mid


for fecha in habiles:
    for vet in (7, 8):
        libre = set(HORARIOS)
        p = DEMANDA_DIA[fecha.weekday()] * DEMANDA_MES[fecha.month]
        for hora in HORARIOS:
            if hora not in libre or R.random() > p * (1.1 if hora < '13:00' else 0.85):
                continue
            pesos = [30, 25 * DEMANDA_MES[fecha.month], 40 if vet == 8 else 30, 6 if hora < '11:00' else 0]
            motivo = R.choices(list(DURACION), pesos)[0]
            b = bloques(hora, motivo)
            if not b or not libre.issuperset(b):
                continue
            libre -= set(b)
            desde_app = motivo != 'Cirugía' and R.random() < 0.55
            t = {'id': len(turnos) + 1, 'mascotaId': mascota_para(motivo, fecha), 'fecha': fecha, 'hora': hora, 'motivo': motivo, 'vetId': vet,
                 'estado': 'pendiente', 'llegada': '', 'sena': SENA if desde_app else ''}
            turnos.append(t)
            pedido = fecha - timedelta(R.randint(1, 12))
            if desde_app and DESDE <= pedido <= HOY:
                nombre = next(m['nombre'] for m in mascotas if m['id'] == t['mascotaId'])
                mov(pedido, f'{R.randint(8, 22):02d}:{R.randint(0, 59):02d}', 'sena', f'Seña · {nombre}, {fecha:%d/%m} {hora}', SENA, 'Mercado Pago', 'App')
        # Días casi llenos: alguien se anota en la lista de espera.
        if fecha <= HOY and len(libre) <= 3 and R.random() < 0.45:
            m = R.choice(mascotas)
            esperas.append({'id': len(esperas) + 1, 'clienteId': m['clienteId'], 'mascotaId': m['id'], 'motivo': R.choice(['Control', 'Vacuna', 'Consulta']),
                            'fecha': fecha, 'vetId': vet if R.random() < 0.5 else '', 'avisado': fecha - timedelta(1) if R.random() < 0.3 else ''})

# Turnos ya pasados: llegada, atención, vacuna aplicada y cobro.
for t in turnos:
    if t['fecha'] > HOY:
        continue
    t['estado'] = 'atendido'
    t['llegada'] = mas(t['hora'], R.choice([-15, -10, -5, -5, 0, 0, 0, 5, 5, 10, 15, 25]))
    m = next(x for x in mascotas if x['id'] == t['mascotaId'])
    monto = PRECIO[t['motivo']] - (t['sena'] or 0)
    vet = next(v['nombre'] for v in VETERINARIOS if v['id'] == t['vetId'])
    mov(t['fecha'], mas(t['hora'], DURACION[t['motivo']]), 'consulta', f"{t['motivo']} · {m['nombre']}", monto,
        R.choices(MEDIOS, [38, 22, 12, 13, 15])[0], vet)

# ---- Tienda: compras según lo que dura cada producto, con reposición de stock ----
compras, mov_stock = [], []
stock = {p['id']: p['stock'] for p in PRODUCTOS}
pedidos = {}  # productoId -> fecha en que llega la reposición
habitos = []
for c in clientes:
    especies = {m['especie'] for m in mascotas if m['clienteId'] == c['id']}
    if 'perro' in especies:
        habitos += [(c['id'], 101, 0.55), (c['id'], 102, 0.5), (c['id'], 103, 0.25)]
    if 'gato' in especies:
        habitos += [(c['id'], 105, 0.6), (c['id'], 101, 0.25)]
    habitos.append((c['id'], 104, 0.3))

ventas = []
for cid, pid, prob in habitos:
    if R.random() > prob:
        continue
    dura = next(p['duraDias'] for p in PRODUCTOS if p['id'] == pid) or 90  # el shampoo no tiene duraDias: cada tanto
    d = DESDE + timedelta(R.randint(0, dura))
    while d <= HOY:
        cant = 2 if pid in (101, 105) and R.random() < 0.15 else 1
        ventas.append((d, cid, pid, cant))
        d += timedelta(round(dura * cant * R.lognormvariate(0, 0.25)))  # a veces vuelve antes, a veces se atrasa

for d, cid, pid, cant in sorted(ventas):
    while d.weekday() >= 5:
        d += timedelta(1)
    if d > HOY:
        continue
    p = next(x for x in PRODUCTOS if x['id'] == pid)
    if pid in pedidos and pedidos[pid] <= d:  # llegó la reposición
        lote = p['minimo'] * 8
        vence = pedidos[pid] + timedelta({101: 270, 102: 540, 103: 720}.get(pid, 900))
        stock[pid] += lote
        mov_stock.append({'id': len(mov_stock) + 1, 'fecha': pedidos[pid], 'productoId': pid, 'cantidad': lote, 'tipo': 'entrada',
                          'detalle': 'Distribuidora del Centro', 'vence': vence if pid in (101, 102, 103) else '', 'por': 'Dra. Paz Ruiz'})
        mov(pedidos[pid], '09:30', 'egreso', f"Proveedor · {p['nombre']} × {lote}", round(lote * p['precio'] * 0.6, -2),
            R.choice(['Efectivo', 'Transferencia']), 'Ana Sosa')
        del pedidos[pid]
    if stock[pid] < cant:  # sin stock: la venta no se hace (y se pide, si no estaba pedido)
        pedidos.setdefault(pid, d + timedelta(R.randint(2, 6)))
        continue
    stock[pid] -= cant
    nombre = next(c['nombre'] for c in clientes if c['id'] == cid)
    mp = R.random() < 0.55
    compras.append({'id': len(compras) + 1, 'clienteId': cid, 'productoId': pid, 'cantidad': cant, 'fecha': d,
                    'pago': 'mercadopago' if mp else 'al_retirar', 'cobrada': True})
    mov_stock.append({'id': len(mov_stock) + 1, 'fecha': d, 'productoId': pid, 'cantidad': -cant, 'tipo': 'venta', 'detalle': nombre, 'vence': '', 'por': 'Tienda'})
    mov(d, f'{R.randint(9, 18):02d}:{R.choice(["05", "20", "35", "50"])}', 'venta', f"{p['nombre']} × {cant} · {nombre}", p['precio'] * cant,
        'Mercado Pago' if mp else R.choice(['Efectivo', 'Débito', 'Transferencia']), 'Tienda' if mp else 'Ana Sosa')
    if stock[pid] <= p['minimo'] and pid not in pedidos:
        pedidos[pid] = d + timedelta(R.randint(2, 6))
    if R.random() < 0.01 and stock[pid] > 0:  # alguno se rompe
        stock[pid] -= 1
        mov_stock.append({'id': len(mov_stock) + 1, 'fecha': d, 'productoId': pid, 'cantidad': -1, 'tipo': 'ajuste', 'detalle': 'Roto', 'vence': '', 'por': 'Ana Sosa'})

# ---- Caja: fondo a la mañana y cierre a la noche, a veces con diferencia ----
cierres = []
for fecha in [d for d in habiles if d <= HOY]:
    mov(fecha, '08:52', 'fondo', 'Fondo de caja', 20000, 'Efectivo', 'Ana Sosa')
    efectivo = sum((-1 if m['tipo'] == 'egreso' else 1) * m['monto'] for m in movimientos if m['fecha'] == fecha and m['medio'] == 'Efectivo')
    contado = efectivo + (R.choice([-1, 1]) * R.randint(1, 20) * 100 if R.random() < 0.08 else 0)
    cierres.append({'fecha': fecha, 'hora': f'19:{R.randint(5, 40):02d}', 'esperado': efectivo, 'contado': contado, 'por': 'Ana Sosa'})
movimientos.sort(key=lambda m: (m['fecha'], m['hora']))
for i, m in enumerate(movimientos, 1):
    m['id'] = i


# ---- Escribir ----
def escribir(nombre, filas):
    SALIDA.mkdir(parents=True, exist_ok=True)
    with open(SALIDA / f'{nombre}.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


for nombre, filas in [('veterinarios', VETERINARIOS), ('clientes', clientes), ('mascotas', mascotas), ('vacunas', vacunas), ('productos', PRODUCTOS),
                      ('turnos', turnos), ('esperas', esperas), ('compras', compras), ('movStock', mov_stock), ('movimientos', movimientos), ('cierres', cierres)]:
    escribir(nombre, filas)
    print(f'{nombre:13} {len(filas):6} filas')
