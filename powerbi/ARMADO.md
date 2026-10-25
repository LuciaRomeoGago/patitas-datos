# Armado del tablero en Power BI

Son cuatro páginas: Agenda, Clínica, Tienda y stock, y Caja. Cada una termina con una decisión.

Los números de cada medida están en `medidas.dax`, para que puedas comprobar que el tablero da lo mismo que los datos.

## 1. Preparar el archivo

1. **Configuración regional.** En *Archivo → Opciones y configuración → Opciones → Archivo actual → Configuración regional*, elegí *Español (Argentina)*. Así toma bien la coma decimal.
2. **Importar las tablas.** Con *Obtener datos → Texto/CSV*, importá las 13 tablas de `datos/modelo`, de a una:
   - Origen del archivo: *65001: Unicode (UTF-8)*.
   - Delimitador: *Punto y coma*.
   - Antes de cargar, entrá a *Transformar datos* y revisá los tipos:
     - Las fechas, como *Fecha*: `fecha`, `semana`, `aplicada`, `proxima`, `vence`, `avisado`.
     - Las columnas con True/False, como *Verdadero/Falso*.
     - `demora`, `diasVencida` y `diasDesdeAnterior`, como *Número decimal*.
3. **Relaciones.** En la vista *Modelo*, todas de uno a varios y con dirección de filtro simple:

   | Desde (uno) | Hacia (varios) |
   |---|---|
   | `dim_fecha[fecha]` | `h_turnos[fecha]`, `h_agenda[fecha]`, `h_vacunas[aplicada]`, `h_ventas[fecha]`, `h_stock[fecha]`, `h_caja[fecha]`, `h_cierres[fecha]`, `h_esperas[fecha]` |
   | `dim_cliente[id]` | `dim_mascota[clienteId]`, `h_ventas[clienteId]` |
   | `dim_mascota[id]` | `h_turnos[mascotaId]`, `h_vacunas[mascotaId]`, `h_esperas[mascotaId]` |
   | `dim_veterinario[id]` | `h_turnos[vetId]`, `h_agenda[vetId]` |
   | `dim_producto[id]` | `h_ventas[productoId]`, `h_stock[productoId]` |

   No relaciones `h_turnos[clienteId]` ni `h_esperas[clienteId]`: el cliente ya llega a través de la mascota, y dos caminos hacia la misma tabla generan una relación ambigua. Si Power BI las crea solo, borralas.
4. **Tabla de fechas.** Marcá `dim_fecha` como tabla de fechas (*Marcar como tabla de fechas*, con la columna `fecha`). Después ordená `diaNombre` por `diaSemana` y `mesNombre` por `mes` (*Ordenar por columna*).
5. **Tema.** En *Vista → Temas → Buscar temas*, elegí `tema-patitas.json`. Tiene la paleta de la app:
   - Fondo beige.
   - Tarjetas blancas con borde.
   - Bosque y Salvia para los datos.
   - Rosa para las alertas.

   Las fuentes Sofia Sans y DM Mono se ven solo si están instaladas en Windows. Si no, Power BI usa otra en su lugar.
6. **Medidas.** Creá una tabla vacía *Medidas* y cargá las de `medidas.dax`. Dales formato:
   - Porcentaje: *Ocupación*, *Llegan 15 min tarde o más*, *Avisados de la lista* y *Recompras tarde*.
   - Moneda, como `$ #.##0`: los montos.
7. **Pie de página.** En cada página, abajo, poné un cuadro de texto chico: *Datos simulados con el modelo de Patitas amigas.*

## 2. Las páginas

Todas usan la misma estructura:
- Arriba, el título y una fila de tarjetas.
- En el medio, dos o tres gráficos.
- Abajo, la decisión en un cuadro de texto con borde Rosa.

### Agenda

**Filtro de página:** `dim_fecha[pasado]` = Verdadero. Sin él, la ocupación se mezcla con días que todavía no pasaron.

**Tarjetas:** Ocupación, Turnos atendidos, Demora promedio (min), Llegan 15 min tarde o más y Avisados de la lista.

**Gráficos:**
- **Columnas: Ocupación por `dim_fecha[diaNombre]`.** Es el gráfico principal. Muestra que el lunes está más lleno que el viernes.
- **Columnas: Turnos atendidos por `h_turnos[hora]`.** Muestra las horas pico: las 9 tiene más del doble que las 18:30.
- **Líneas: Ocupación por `dim_fecha[anioMes]`,** con una línea por `dim_veterinario[nombre]`.

> **Decisión:** Los viernes la agenda está al 47 % y los lunes, al 61 %. Ofrecer primero el viernes en los recordatorios de vacunas y controles. También conviene avisarle a toda la lista de espera: hoy se le avisa a 4 de cada 10.

### Clínica

Sin filtro de página. Si lo ponés, se pierden las vacunas vencidas que se aplicaron antes del período.

**Tarjetas:** Vacunas aplicadas (con filtro de visual `dim_fecha[pasado]` = Verdadero) y Vacunas para avisar.

**Gráficos:**
- **Columnas: Vacunas aplicadas por `dim_fecha[anioMes]`,** con el mismo filtro de visual. Muestra el pico de primavera.
- **Barras agrupadas: Consultas por `h_turnos[motivo]`,** con leyenda `dim_mascota[especie]`.
- **Tabla "A quién avisar":**
  - Columnas: `dim_cliente[nombre]`, `dim_cliente[telefono]`, `dim_mascota[nombre]`, `h_vacunas[nombre]`, `h_vacunas[proxima]` y `h_vacunas[diasVencida]`.
  - Filtro de visual: `h_vacunas[avisar]` = Verdadero.
  - Orden: por `diasVencida`, de mayor a menor.

> **Decisión:** Hay 131 vacunas vencidas sin turno: avisar esta semana a esos dueños desde la app (la tabla es la lista). Además, reforzar la agenda de vacunas en septiembre y octubre, cuando se aplican más del doble que en verano.

### Tienda y stock

**Tarjetas:** Ventas, Unidades vendidas, Recompras tarde, Productos bajo el mínimo y Lotes por vencer en 60 días.

**Gráficos:**
- **Barras horizontales: Ventas por `dim_producto[nombre]`.** Lo que más rota.
- **Columnas apiladas al 100 %:** cantidad de `h_ventas[id]` por `dim_producto[nombre]`, con leyenda `h_ventas[recompra]`.
  - Filtro de visual: `recompra` en *A tiempo* y *Tarde*.
  - Colores: Salvia para *A tiempo*, Rosa para *Tarde*.
- **Columnas apiladas: Días sin stock por `dim_fecha[anioMes]`,** con leyenda `dim_producto[nombre]`.
- **Tabla de stock:** `dim_producto[nombre]`, `stockActual`, `minimo` y `bajoMinimo`, con formato condicional en Rosa cuando `bajoMinimo` es Verdadero.

> **Decisión:** La arena y el alimento estuvieron 28 días sin stock en el año. Se venden unos 5 o 6 por día hábil y el pedido tarda hasta 6 días, así que conviene subir el mínimo de los dos a unos 30 (hoy es 5 y 6) para pedir antes de quedarse sin stock. Además, 3 de cada 10 recompras llegan tarde: avisar al cliente cuando se le está por terminar.

### Caja

**Filtro de página:** `dim_fecha[pasado]` = Verdadero.

**Tarjetas:** Cobrado, Gastos, Señas cobradas y Cierres con diferencia.

**Gráficos:**
- **Columnas apiladas: Cobrado por `dim_fecha[anioMes]`,** con leyenda `h_caja[tipo]`.
- **Barras horizontales: Cobrado por `h_caja[medio]`.** Mercado Pago es el 43 %.
- **Columnas: `h_cierres[diferencia]` por `h_cierres[fecha]`.** Formato condicional: Rosa si es negativa, Salvia si es positiva.

> **Decisión:** 22 cierres tuvieron diferencia, de hasta $ 2.000. Sumar un conteo de caja al mediodía, así el error se encuentra el mismo día y no a la noche.

## 3. Capturas

1. Exportá cada página a imagen. Por ejemplo, en *Archivo → Exportar → PDF* y después pasás cada hoja a imagen, o hacés una captura de pantalla con el lienzo en *Ajustar a la página*.
2. Guardalas en `capturas/` con estos nombres: `agenda.png`, `clinica.png`, `tienda.png` y `caja.png`.
3. Sumá también una captura de la vista *Modelo*, `modelo.png`, que muestra el modelo en estrella.
