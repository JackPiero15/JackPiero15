# Números

## Conceptos

- **CPA (costo por adquisición):** gasto en anuncios ÷ ventas confirmadas.
- **CPA límite:** lo máximo que puedes pagar en anuncios por una venta sin perder. Es tu margen antes de publicidad.
- **CPA óptimo u objetivo:** el CPA que deja la utilidad que quieres.
- **ROAS:** ingreso ÷ gasto en anuncios. ROAS de equilibrio = ingreso ÷ CPA límite. El mentor mide más por CPA que por ROAS.
- Métricas duras (CPA, ROAS, utilidad) primero; métricas blandas (CTR, tasa de conversión, CPM) después, para diagnosticar.

Ejemplo del mentor: ticket promedio con upsells S/ 149 → CPA óptimo S/ 15, CPA límite S/ 20. Si el CPA pasa de 20, cada venta pierde dinero aunque el Shopify muestre muchos pedidos.

## Fórmulas (las mismas de `scripts/calculadora.py`)

Por venta confirmada (cerrada y despachada):

```
ingreso cobrado      = ticket × tasa de recojo
CPA límite           = ticket × recojo − costo producto × recojo − envío − otros − comisión
CPA objetivo         = CPA límite − margen objetivo × ingreso cobrado
costo máx. mensaje   = CPA objetivo × tasa de cierre
ROAS de equilibrio   = ingreso cobrado ÷ CPA límite
utilidad por venta   = CPA límite − CPA actual
ventas al día (meta) = (gastos fijos + utilidad deseada) ÷ utilidad por venta ÷ 30
mensajes al día      = ventas al día ÷ tasa de cierre
gasto en ads al día  = ventas al día × CPA actual
```

Supuestos (conservadores): los pedidos no recogidos vuelven al stock; el envío se paga en todos los pedidos despachados; no se cuenta el adelanto retenido cuando no recogen. La comisión se paga por venta cerrada.

Ejemplo con valores por defecto (ticket 139, costo 30, envío 12, otros 3, comisión 3, recojo 90%, cierre 7%, CPA actual 25, margen 20%, fijos 3,000, meta 5,000):
- ingreso cobrado S/ 125.10; CPA límite S/ 80.10; CPA objetivo S/ 55.08
- costo máximo por mensaje S/ 3.86 (≈ US$ 1.13)
- ROAS de equilibrio 1.56; utilidad por venta S/ 55.10
- ~4.8 ventas al día, ~69 mensajes al día, ~S/ 121 al día en anuncios

## Cómo leer el resultado con el usuario

- CPA límite ≤ 0 → el producto no deja margen: subir ticket (packs), bajar costo o cambiar producto.
- CPA actual ≥ CPA límite → pierde en cada venta: parar de escalar, arreglar creativos, oferta o cierre.
- CPA actual entre objetivo y límite → gana poco: mejorar cierre o ticket antes de escalar.
- CPA actual < objetivo → rentable: puede subir presupuesto mientras se mantenga.
- Anuncios como % del ticket: sano 10–15%; más de 30% es alarma.

## Cifras de referencia del mentor

Son de sus negocios en Perú; sirven para saber si un número es raro, no como promesa.

| Métrica | Referencia |
|---|---|
| Costo por mensaje (WhatsApp, Meta) | US$ 0.20–0.70; con objetivo Interacción US$ 0.10–0.20 |
| Cierre sobre mensajes | 5–8% (12% en un día excepcional) |
| Cierre sobre leads de formulario | 20–30% bueno; meta 40% nacional, 60–70% Lima |
| Recojo en provincia | 90–95% con adelanto de 30% o más; ~85% con S/ 10–20 |
| CPA en Latinoamérica | US$ 3–7 (su marca de probióticos US$ 5–8); en EE.UU. US$ 25+ |
| Anuncios / facturación | 10–15% ideal; promedio de e-commerce más de 30% |
| Utilidad neta | 30–40% (marca con recompra); en Colombia productos de 15–30% |
| Recompra | ~30% de la facturación |
| Visita al perfil (marcas, tráfico frío) | ≤ US$ 0.03–0.04 |
| Costo por seguidor (campaña de seguidores) | ~US$ 0.43 |
| CTR en Facebook | más de 2% |
| Relación CPM:CTR | 2:1 o mejor; 3:1 o peor es alarma |
| Tasa de acierto de creativos | 20–40% con proceso |
| Testeo por producto | US$ 3–10 diarios para quien empieza; él US$ 30–50 |
| Tipo de cambio que usaba | S/ 3.4 por dólar |
| Ticket típico de sus marcas | S/ 119–149 |

Para un reto de facturación, calcula hacia atrás: meta ÷ días = facturación diaria; ÷ ticket = pedidos diarios; ÷ cierre = mensajes diarios; × costo por mensaje = presupuesto diario; ÷ 200 mensajes por asesora = asesoras necesarias.
