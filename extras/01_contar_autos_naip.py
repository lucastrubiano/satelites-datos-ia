"""Cuenta autos en un estacionamiento con imagen aérea NAIP (60 cm) y YOLO OBB preentrenado en DOTA.

Sin probar de punta a punta: ajustar bbox y conf antes de usarlo en vivo.
"""
import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from ultralytics import YOLO

# bbox lon/lat del estacionamiento (ejemplo: reemplazar por el local elegido)
BBOX = [-122.3405, 37.9330, -122.3375, 37.9350]
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

# 1) Buscar NAIP sobre el estacionamiento
cat = pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)
items = list(cat.search(collections=["naip"], bbox=BBOX).items())
item = sorted(items, key=lambda i: i.datetime)[-1]  # la más reciente

# 2) Recortar solo el estacionamiento (COG: lee solo esa ventana)
with rasterio.open(item.assets["image"].href) as src:
    b = transform_bounds("EPSG:4326", src.crs, *BBOX)
    img = src.read([1, 2, 3], window=from_bounds(*b, src.transform))
rgb = np.ascontiguousarray(np.moveaxis(img, 0, -1))

# 3) Detectar. NAIP es 60 cm; en DOTA los objetos son más grandes en píxeles: subir escala ayuda
model = YOLO("yolo11n-obb.pt")  # preentrenado en DOTAv1
res = model.predict(rgb, imgsz=1280, conf=0.25)[0]
autos = [c for c in res.obb.cls.tolist() if res.names[int(c)] == "small vehicle"]
print(f"{item.datetime.date()}: {len(autos)} autos")
res.save("conteo.png")  # imagen con las cajas
