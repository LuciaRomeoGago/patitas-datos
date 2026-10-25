"""
Limpia los datos crudos y arma el modelo en estrella para Power BI.

Hechos: turnos, agenda (minutos ocupados por día y veterinario), vacunas, ventas, stock, caja,
cierres y lista de espera. Dimensiones: fecha, cliente, mascota, veterinario y producto.
Antes de escribir, controla que los datos cumplan las reglas de la app (ver `controlar`).

Uso: python scripts/preparar.py   (lee datos/crudos, escribe datos/modelo)
Los CSV van con ; y coma decimal, como el Excel del Resumen del mes de la app.
"""
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CRUDOS, MODELO = RAIZ / 'datos' / 'crudos', RAIZ / 'datos' / 'modelo'
HOY = pd.Timestamp('2026-09-30')  # el mismo "hoy" que generar_datos.py
DURACION = {'Control': 30, 'Vacuna': 30, 'Consulta': 60, 'Cirugía': 120}
MINUTOS_POR_DIA = 390  # 9 a 12:30 y 16 a 19
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def leer(nombre, fechas=()):
    return pd.read_csv(CRUDOS / f'{nombre}.csv', parse_dates=list(fechas))


def minutos(hora):
    return hora.str[:2].astype(int) * 60 + hora.str[3:].astype(int)


vets, clientes, mascotas, productos = leer('veterinarios'), leer('clientes'), leer('mascotas'), leer('productos')
turnos = leer('turnos', ['fecha'])
vacunas = leer('vacunas', ['aplicada', 'proxima'])
compras = leer('compras', ['fecha'])
stock = leer('movStock', ['fecha', 'vence'])
caja = leer('movimientos', ['fecha'])
cierres = leer('cierres', ['fecha'])
esperas = leer('esperas', ['fecha', 'avisado'])

# ---- Dimensión fecha ----
fechas = pd.DataFrame({'fecha': pd.date_range(min(caja.fecha.min(), turnos.fecha.min()), turnos.fecha.max())})
fechas['anio'] = fechas.fecha.dt.year
fechas['mes'] = fechas.fecha.dt.month
fechas['mesNombre'] = fechas.mes.map(lambda m: MESES[m - 1])
fechas['anioMes'] = fechas.fecha.dt.strftime('%Y-%m')
fechas['semana'] = fechas.fecha - pd.to_timedelta(fechas.fecha.dt.weekday, unit='D')  # lunes de esa semana
fechas['diaSemana'] = fechas.fecha.dt.weekday + 1  # 1 = lunes, para ordenar
fechas['diaNombre'] = fechas.fecha.dt.weekday.map(lambda d: DIAS[d])
fechas['habil'] = fechas.fecha.dt.weekday < 5
fechas['pasado'] = fechas.fecha <= HOY

# ---- Turnos y agenda ----
turnos = turnos.merge(mascotas[['id', 'clienteId']].rename(columns={'id': 'mascotaId'}), on='mascotaId', how='left')
turnos['duracion'] = turnos.motivo.map(DURACION)
turnos['inicio'] = minutos(turnos.hora)
turnos['franja'] = turnos.inicio.lt(13 * 60).map({True: 'Mañana', False: 'Tarde'})
llegada = turnos.llegada.fillna('00:00')
turnos['demora'] = (minutos(llegada) - turnos.inicio).where(turnos.llegada.notna())  # minutos después de la hora (negativo: llegó antes)
turnos['conSena'] = turnos.sena.notna()
turnos['sena'] = turnos.sena.fillna(0).astype(int)

agenda = (fechas[fechas.habil][['fecha']].merge(vets[vets.rol == 'veterinario'][['id']].rename(columns={'id': 'vetId'}), how='cross')
          .merge(turnos.groupby(['fecha', 'vetId'], as_index=False).agg(minutosOcupados=('duracion', 'sum'), turnos=('id', 'count')), how='left')
          .fillna({'minutosOcupados': 0, 'turnos': 0}))
agenda['minutosDisponibles'] = MINUTOS_POR_DIA
agenda[['minutosOcupados', 'turnos']] = agenda[['minutosOcupados', 'turnos']].astype(int)

# ---- Vacunas: la última dosis de cada una dice si está vencida y si ya tiene turno ----
vacunas = vacunas.sort_values('aplicada').reset_index(drop=True)
vacunas['id'] = vacunas.index + 1
vacunas['ultima'] = ~vacunas.duplicated(['mascotaId', 'nombre'], keep='last')
con_turno = set(turnos[(turnos.motivo == 'Vacuna') & (turnos.fecha > HOY)].mascotaId)
vacunas['vencida'] = vacunas.ultima & (vacunas.proxima < HOY)
vacunas['conTurno'] = vacunas.mascotaId.isin(con_turno)
vacunas['avisar'] = vacunas.vencida & ~vacunas.conTurno
vacunas['diasVencida'] = (HOY - vacunas.proxima).dt.days.where(vacunas.vencida)

# ---- Ventas: importe y si la recompra llegó a tiempo según lo que dura el producto ----
ventas = compras.merge(productos[['id', 'precio', 'duraDias']].rename(columns={'id': 'productoId'}), on='productoId').sort_values(['clienteId', 'productoId', 'fecha'])
ventas['importe'] = ventas.precio * ventas.cantidad
previa = ventas.groupby(['clienteId', 'productoId'])
ventas['diasDesdeAnterior'] = previa.fecha.diff().dt.days
debia = ventas.duraDias * previa.cantidad.shift()  # lo que tenía que durar lo de la compra anterior
ventas['recompra'] = 'Primera'
ventas.loc[ventas.diasDesdeAnterior.notna() & ventas.duraDias.notna(), 'recompra'] = 'A tiempo'
ventas.loc[ventas.diasDesdeAnterior > debia + 5, 'recompra'] = 'Tarde'
ventas.loc[ventas.duraDias.isna() & ventas.diasDesdeAnterior.notna(), 'recompra'] = 'Sin duración'
ventas = ventas.drop(columns=['precio', 'duraDias']).sort_values('id')

# ---- Stock: cómo queda después de cada movimiento ----
stock = stock.sort_values(['fecha', 'id'])
stock['stockDespues'] = stock.groupby('productoId').cantidad.cumsum() + stock.productoId.map(productos.set_index('id').stock)
actual = stock.groupby('productoId').stockDespues.last()
productos['stockActual'] = productos.id.map(actual).fillna(productos.stock).astype(int)
productos['bajoMinimo'] = productos.stockActual <= productos.minimo
stock['venceEn60'] = stock.vence.between(HOY, HOY + pd.Timedelta(days=60))

# ---- Caja y cierres ----
caja['importe'] = caja.monto.where(caja.tipo != 'egreso', -caja.monto)  # con signo: los gastos restan
caja['esCobro'] = ~caja.tipo.isin(['fondo', 'egreso'])
cierres['diferencia'] = cierres.contado - cierres.esperado

esperas['avisada'] = esperas.avisado.notna()


def controlar():
    # Sin turnos superpuestos para el mismo veterinario.
    for (f, v), g in turnos.sort_values('inicio').groupby(['fecha', 'vetId']):
        fin = g.inicio + g.duracion
        assert (g.inicio.iloc[1:].to_numpy() >= fin.iloc[:-1].to_numpy()).all(), f'turnos superpuestos el {f:%d/%m/%Y} con {v}'
    # Dentro de la agenda: lunes a viernes, de 9 a 12:30 o de 16 a 19.
    fin = turnos.inicio + turnos.duracion
    assert (turnos.fecha.dt.weekday < 5).all(), 'turno en fin de semana'
    assert (((turnos.inicio >= 540) & (fin <= 750)) | ((turnos.inicio >= 960) & (fin <= 1140))).all(), 'turno fuera de horario'
    assert (stock.stockDespues >= 0).all(), 'stock negativo'
    assert (caja.monto > 0).all(), 'monto de caja no positivo'
    assert turnos.clienteId.notna().all() and ventas.clienteId.isin(clientes.id).all(), 'referencia rota'
    assert (agenda.minutosOcupados <= agenda.minutosDisponibles).all(), 'agenda pasada de minutos'


controlar()

MODELO.mkdir(parents=True, exist_ok=True)
tablas = {
    'dim_fecha': fechas,
    'dim_cliente': clientes,
    'dim_mascota': mascotas,
    'dim_veterinario': vets,
    'dim_producto': productos,
    'h_turnos': turnos.drop(columns=['inicio']),
    'h_agenda': agenda,
    'h_vacunas': vacunas,
    'h_ventas': ventas,
    'h_stock': stock,
    'h_caja': caja,
    'h_cierres': cierres,
    'h_esperas': esperas,
}
for nombre, df in tablas.items():
    df.to_csv(MODELO / f'{nombre}.csv', sep=';', decimal=',', index=False, encoding='utf-8-sig', date_format='%Y-%m-%d')
    print(f'{nombre:16} {len(df):6} filas')
print('Controles: ok')
