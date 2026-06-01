#!/usr/bin/env python3
"""Gera a máscara binária de terra (dotmap) embutida no index.html.

Fonte: GeoJSON ne_110m_land (Natural Earth, domínio público).
  curl -sL -o /tmp/ne_land.geojson \
    https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson

Saída: JSON com {cols, rows, w, h, latTop, latBot, mask(base64)}.
O `mask` é uma sequência de bits row-major (1 = terra) numa grade equiretangular
recortada em latitude [latBot, latTop]. O index.html decodifica e desenha um ponto
por célula de terra no <canvas>.

Uso:
  python3 gen_dotmap.py /tmp/ne_land.geojson > dotmap.json
"""
import json, base64, sys

W = 1000.0
LAT_TOP, LAT_BOT = 85.0, -60.0   # recorta Antártida + extremo norte
COLS = 200

def main(path):
    H = W * (LAT_TOP - LAT_BOT) / 360.0
    ROWS = int(round(H / (W / COLS)))
    H = round(H)

    with open(path) as f:
        gj = json.load(f)

    rings = []
    for feat in gj['features']:
        geom = feat['geometry']
        polys = ([geom['coordinates']] if geom['type'] == 'Polygon'
                 else geom['coordinates'] if geom['type'] == 'MultiPolygon' else [])
        for poly in polys:
            for ring in poly:
                rings.append([(pt[0], pt[1]) for pt in ring])

    def inside(lon, lat):
        res = False
        for ring in rings:
            n = len(ring); j = n - 1
            for i in range(n):
                xi, yi = ring[i]; xj, yj = ring[j]
                if ((yi > lat) != (yj > lat)) and \
                   (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
                    res = not res
                j = i
        return res

    bits = bytearray(); cur = 0; nbit = 0
    for r in range(ROWS):
        lat = LAT_TOP - (r + 0.5) * (LAT_TOP - LAT_BOT) / ROWS
        for c in range(COLS):
            lon = -180 + (c + 0.5) * 360.0 / COLS
            cur = (cur << 1) | (1 if inside(lon, lat) else 0)
            nbit += 1
            if nbit == 8:
                bits.append(cur); cur = 0; nbit = 0
    if nbit:
        bits.append(cur << (8 - nbit))

    print(json.dumps({
        "cols": COLS, "rows": ROWS, "w": int(W), "h": H,
        "latTop": LAT_TOP, "latBot": LAT_BOT,
        "mask": base64.b64encode(bytes(bits)).decode()
    }))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/tmp/ne_land.geojson')
