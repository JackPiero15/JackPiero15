#!/usr/bin/env python3
"""Calculadora de números para e-commerce contraentrega.

Calcula, por venta confirmada: ingreso cobrado, CPA límite, CPA objetivo,
costo máximo por mensaje, ROAS de equilibrio, utilidad por venta y cuántas
ventas, mensajes y presupuesto diario se necesitan para una meta mensual.

Supuestos (conservadores): los pedidos no recogidos vuelven al stock, el envío
se paga en todos los pedidos despachados y no se cuenta el adelanto retenido
cuando el cliente no recoge. La comisión se paga por venta cerrada.

Ejemplo:
  python calculadora.py --precio 139 --costo 30 --envio 12 --recojo 90 --cierre 7 --cpa 25
  python calculadora.py --precio 89 --costo 22 --json
"""

import argparse
import json
import sys


def calcular(precio, costo, envio, otros, comision, recojo, cierre, cpa,
             margen, fijos, meta, tc):
    r = min(max(recojo, 0.0), 100.0) / 100.0
    t = min(max(cierre, 0.0), 100.0) / 100.0
    m = min(max(margen, 0.0), 90.0) / 100.0

    ingreso = precio * r
    limite = ingreso - costo * r - envio - otros - comision
    objetivo = limite - m * ingreso
    utilidad = limite - cpa

    res = {
        "ingreso_cobrado": ingreso,
        "cpa_limite": limite,
        "cpa_objetivo": objetivo,
        "costo_max_mensaje": objetivo * t if objetivo > 0 and t > 0 else None,
        "costo_limite_mensaje": limite * t if limite > 0 and t > 0 else None,
        "roas_equilibrio": ingreso / limite if limite > 0 else None,
        "utilidad_por_venta": utilidad,
        "anuncios_pct_ticket": cpa / precio * 100 if precio > 0 else None,
        "ventas_dia": None,
        "mensajes_dia": None,
        "gasto_ads_dia": None,
        "facturacion_mes": None,
    }
    if utilidad > 0:
        ventas_mes = (fijos + meta) / utilidad
        dia = ventas_mes / 30.0
        res["ventas_dia"] = dia
        res["mensajes_dia"] = dia / t if t > 0 else None
        res["gasto_ads_dia"] = dia * cpa
        res["facturacion_mes"] = ventas_mes * precio

    if limite <= 0:
        estado = ("SIN MARGEN", "Con este precio y estos costos no queda nada para anuncios. "
                  "Sube el ticket (packs), baja el costo o cambia de producto.")
    elif cpa >= limite:
        estado = ("PIERDES EN CADA VENTA", "Tu CPA actual es mayor que tu CPA límite. "
                  "Arregla creativos, oferta o cierre antes de gastar más.")
    elif cpa > objetivo:
        estado = ("GANAS, PERO POCO", "Estás entre el CPA objetivo y el límite: no pierdes, "
                  "pero no llegas a tu margen. Mejora el cierre o el ticket antes de escalar.")
    else:
        estado = ("RENTABLE", "Tu CPA actual está por debajo del objetivo. "
                  "Puedes subir presupuesto mientras se mantenga así.")
    res["estado"], res["explicacion"] = estado
    res["tipo_cambio"] = tc
    return res


def soles(v):
    return "–" if v is None else f"S/ {v:,.2f}"


def main(argv=None):
    p = argparse.ArgumentParser(description="Calculadora de CPA para e-commerce contraentrega")
    p.add_argument("--precio", type=float, default=139, help="ticket promedio en soles (con packs)")
    p.add_argument("--costo", type=float, default=30, help="costo del producto puesto en almacén")
    p.add_argument("--envio", type=float, default=12, help="envío por pedido despachado")
    p.add_argument("--otros", type=float, default=3, help="empaque, etiqueta, bono impreso")
    p.add_argument("--comision", type=float, default=3, help="comisión por venta cerrada")
    p.add_argument("--recojo", type=float, default=90, help="tasa de recojo/entrega en %%")
    p.add_argument("--cierre", type=float, default=7, help="tasa de cierre de mensajes o leads en %%")
    p.add_argument("--cpa", type=float, default=25, help="CPA actual en soles (gasto ads / ventas)")
    p.add_argument("--margen", type=float, default=20, help="margen objetivo sobre lo cobrado en %%")
    p.add_argument("--fijos", type=float, default=3000, help="gastos fijos mensuales")
    p.add_argument("--meta", type=float, default=5000, help="utilidad mensual deseada")
    p.add_argument("--tc", type=float, default=3.4, help="soles por dólar")
    p.add_argument("--json", action="store_true", help="salida en JSON")
    a = p.parse_args(argv)

    res = calcular(a.precio, a.costo, a.envio, a.otros, a.comision, a.recojo, a.cierre,
                   a.cpa, a.margen, a.fijos, a.meta, a.tc)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if a.json:
        redondeado = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in res.items()}
        print(json.dumps(redondeado, ensure_ascii=False, indent=2))
        return

    tc = a.tc if a.tc > 0 else 3.4
    msg = res["costo_max_mensaje"]
    lines = [
        f"Datos: ticket S/ {a.precio:g} · costo S/ {a.costo:g} · envío S/ {a.envio:g} · otros S/ {a.otros:g} · "
        f"comisión S/ {a.comision:g} · recojo {a.recojo:g}% · cierre {a.cierre:g}% · CPA actual S/ {a.cpa:g} · "
        f"margen objetivo {a.margen:g}%",
        "",
        f"Estado: {res['estado']}",
        res["explicacion"],
        "",
        f"Ingreso cobrado por venta ........ {soles(res['ingreso_cobrado'])}",
        f"CPA límite (equilibrio) .......... {soles(res['cpa_limite'])}",
        f"CPA objetivo ..................... {soles(res['cpa_objetivo'])}",
        f"Costo máximo por mensaje ......... {soles(msg)}" + (f" (US$ {msg / tc:.2f})" if msg else ""),
        f"Costo límite por mensaje ......... {soles(res['costo_limite_mensaje'])}",
        f"ROAS de equilibrio ............... " + ("–" if res["roas_equilibrio"] is None else f"{res['roas_equilibrio']:.2f}x"),
        f"Utilidad por venta (CPA actual) .. {soles(res['utilidad_por_venta'])}",
        f"Anuncios como % del ticket ....... " + ("–" if res["anuncios_pct_ticket"] is None else f"{res['anuncios_pct_ticket']:.1f}% (sano 10–15%, alarma +30%)"),
    ]
    if res["ventas_dia"] is not None:
        lines += [
            "",
            f"Para cubrir S/ {a.fijos:,.0f} de fijos + S/ {a.meta:,.0f} de utilidad al mes:",
            f"  Ventas al día ..... {res['ventas_dia']:.1f}",
            f"  Mensajes al día ... " + ("–" if res["mensajes_dia"] is None else f"{res['mensajes_dia']:.0f}"),
            f"  Anuncios al día ... {soles(res['gasto_ads_dia'])} (US$ {res['gasto_ads_dia'] / tc:,.0f})",
            f"  Facturación al mes  {soles(res['facturacion_mes'])}",
        ]
    lines += ["", "Supuestos: no recogidos vuelven al stock; envío pagado en todo despacho; no se cuenta el adelanto retenido."]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
