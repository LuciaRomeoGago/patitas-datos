# Patitas amigas · Datos

Un año de datos de la veterinaria, preparados con Python (pandas) para un tablero de Power BI. Sale de la app [Patitas amigas](https://github.com/LuciaRomeoGago/Veterinaria-Patitas-Amigas) y usa su mismo modelo de datos (`src/data/types.ts`).

> **Los datos son simulados.** Los genera un script con las reglas de la app. No son datos reales de una veterinaria.

## Cómo se generan

```bash
pip install pandas
python scripts/generar_datos.py   # datos/crudos: una tabla por entidad de la app
python scripts/preparar.py        # datos/modelo: el modelo en estrella para Power BI
```

`generar_datos.py` usa una semilla fija, así que siempre genera los mismos datos.

**Período:**
- Los datos van del 1/10/2025 al 30/9/2026.
- El "hoy" del tablero es el 30/9/2026.
- Los turnos de las tres semanas siguientes quedan pendientes.

**Reglas de la app que respetan los datos:**
- La agenda es de lunes a viernes, de 9 a 12:30 y de 16 a 19, en bloques de 30 minutos.
- Control y Vacuna duran 30 minutos, Consulta 1 hora y Cirugía 2 horas.
- Al pedir turno desde la app se paga una seña de $5.000, que se descuenta del cobro.
- Los precios son los mismos de la app.

**Lo que se simula:**
- Más demanda a la mañana, los lunes y en primavera.
- Las vacunas se aplican cuando les toca. Algunas quedan vencidas y sin turno.
- Las recompras siguen lo que dura cada producto (`duraDias`): a veces llegan antes y a veces tarde.
- La reposición de stock se pide cuando se llega al mínimo. Mientras tanto, a veces se queda sin stock y esas ventas no se hacen.
- La caja se abre con un fondo y se cierra al final del día. Algunos cierres tienen diferencia.

**Fuera de alcance:** la app no registra ausencias, reprogramaciones ni si un turno salió de la lista de espera. Por eso el tablero no los mide. De la lista de espera se mide cuántas personas se anotaron y a cuántas se les avisó.

`preparar.py` controla estas reglas antes de escribir el modelo. Si alguna falla, el script se corta:
- No hay turnos superpuestos para el mismo veterinario.
- Todos los turnos están dentro del horario.
- El stock nunca queda negativo.
- Los montos de caja son positivos.
- No hay referencias rotas entre tablas.

## Modelo para Power BI

Los CSV de `datos/modelo` usan `;` como separador, coma decimal y codificación UTF-8, igual que el Excel del Resumen del mes de la app.

Para importarlos en Power BI: *Obtener datos → Texto/CSV*, con origen *65001: Unicode (UTF-8)*, delimitador *Punto y coma* y configuración regional *Español (Argentina)*.

| Tabla | Una fila por | Se relaciona con |
|---|---|---|
| `dim_fecha` | día | todas las tablas de hechos, por la fecha |
| `dim_cliente` | cliente | `dim_mascota` y `h_ventas` (`clienteId`); a los turnos llega por la mascota |
| `dim_mascota` | mascota | `h_turnos`, `h_vacunas`, `h_esperas` (`mascotaId`) |
| `dim_veterinario` | integrante del equipo | `h_turnos`, `h_agenda` (`vetId`) |
| `dim_producto` | producto (con `stockActual` y `bajoMinimo`) | `h_ventas`, `h_stock` (`productoId`) |
| `h_turnos` | turno (`duracion`, `franja`, `demora` en minutos, `conSena`) | |
| `h_agenda` | día hábil y veterinario (`minutosOcupados`, `minutosDisponibles`) | |
| `h_vacunas` | dosis aplicada (`ultima`, `vencida`, `conTurno`, `avisar`) | `dim_fecha` por `aplicada` |
| `h_ventas` | compra (`importe`, `recompra`: Primera, A tiempo, Tarde) | |
| `h_stock` | movimiento de stock (`stockDespues`; en las entradas, `quedan` del lote y `venceEn60`) | |
| `h_caja` | movimiento de caja (`importe` con signo, `esCobro`) | |
| `h_cierres` | cierre de caja (`diferencia`) | |
| `h_esperas` | anotación en la lista de espera (`avisada`) | |

**Cómo leer algunas columnas:**
- La ocupación es `SUM(h_agenda[minutosOcupados]) / SUM(h_agenda[minutosDisponibles])`.
- La `demora` es lo que tardó en llegar respecto de la hora del turno. Si es negativa, llegó antes.
- `avisar` marca las vacunas vencidas cuya mascota no tiene un turno de vacuna pedido: son los clientes a quienes conviene avisarles.

## Tablero

El tablero es el proyecto de Power BI `powerbi/patitas.pbip` (se abre con Power BI Desktop). Las capturas de las cuatro páginas y del modelo están en `capturas/`.

En `powerbi/` también están el tema con la paleta de la app (`tema-patitas.json`), las medidas en DAX con el valor que tiene que dar cada una (`medidas.dax`) y el armado de las cuatro páginas, con la decisión de cada una (`ARMADO.md`).
