import os
import json
import logging
from shapely.geometry import shape, mapping
from pyproj import Transformer

logger = logging.getLogger("boundaries")

DATA_DIR = os.path.join(os.path.dirname(__file__), "src", "dashboard", "data")
os.makedirs(DATA_DIR, exist_ok=True)

class BoundaryService:
    def __init__(self):
        self._cache = {}
        
    def _read_shp_to_geojson(self, shp_path, out_geojson_path):
        """Reads a shapefile, handles coordinate transforms if UTM, and saves/returns GeoJSON."""
        if os.path.exists(out_geojson_path) and os.path.getsize(out_geojson_path) > 100:
            try:
                with open(out_geojson_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading cached {out_geojson_path}: {e}")

        if not os.path.exists(shp_path):
            logger.warning(f"Shapefile not found: {shp_path}")
            return None

        try:
            import shapefile
            sf = shapefile.Reader(shp_path)
            fields = [f[0] for f in sf.fields[1:]]
            
            features = []
            for shape_rec in sf.shapeRecords():
                geom = shape_rec.shape.__geo_interface__
                props = dict(zip(fields, shape_rec.record))
                
                clean_props = {}
                for k, v in props.items():
                    if isinstance(v, bytes):
                        clean_props[k] = v.decode('utf-8', errors='ignore')
                    elif isinstance(v, (int, float, str, bool)) or v is None:
                        clean_props[k] = v
                    else:
                        clean_props[k] = str(v)

                geom_obj = shape(geom)
                bounds = geom_obj.bounds
                
                # Check if coordinates need reprojecting from UTM / Gauss / Arc1950 to WGS84
                if bounds[0] > 180 or bounds[1] < -100 or bounds[0] < -180:
                    for test_epsg in ["EPSG:32735", "EPSG:32736", "EPSG:20935", "EPSG:20936"]:
                        try:
                            trans = Transformer.from_crs(test_epsg, "EPSG:4326", always_xy=True)
                            from shapely.ops import transform
                            reproj = transform(trans.transform, geom_obj)
                            b = reproj.bounds
                            # Zimbabwe bounds: lat -23.0 to -15.0, lon 24.5 to 33.5
                            if 24.0 <= b[0] <= 34.0 and -23.0 <= b[1] <= -15.0:
                                geom = mapping(reproj)
                                break
                        except Exception:
                            pass
                
                features.append({
                    "type": "Feature",
                    "properties": clean_props,
                    "geometry": geom
                })
                
            fc = {
                "type": "FeatureCollection",
                "features": features
            }
            
            with open(out_geojson_path, "w", encoding="utf-8") as f:
                json.dump(fc, f)
                
            return fc
        except Exception as e:
            logger.error(f"Error converting shapefile {shp_path}: {e}")
            return None

    def get_provinces(self):
        if "provinces" in self._cache:
            return self._cache["provinces"]
            
        out_path = os.path.join(DATA_DIR, "provinces.geojson")
        admin_base = r"F:\MTN - Main Desktop\Masters GIS  - Brandon Comp Science\Practical Assignment 5 (Fire Density)\data\extracted"
        src_path = os.path.join(admin_base, "zwe_admin1.shp")
        alt_path = r"F:\MTN - Main Desktop\Masters GIS  - Brandon Comp Science\MASTERS LULC - Brandon Comp Scince\GEE_Upload_Shapefiles\Provinces.shp"
        
        # Check cached GeoJSON first
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache["provinces"] = data
                    return data
            except Exception:
                pass

        data = self._read_shp_to_geojson(src_path, out_path)
        if not data and os.path.exists(alt_path):
            data = self._read_shp_to_geojson(alt_path, out_path)
            
        if not data:
            data = self._generate_fallback_provinces()
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

        self._cache["provinces"] = data
        return data

    def get_districts(self):
        if "districts" in self._cache:
            return self._cache["districts"]
            
        out_path = os.path.join(DATA_DIR, "districts.geojson")
        admin_base = r"F:\MTN - Main Desktop\Masters GIS  - Brandon Comp Science\Practical Assignment 5 (Fire Density)\data\extracted"
        src_path = os.path.join(admin_base, "zwe_admin2.shp")
        
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache["districts"] = data
                    return data
            except Exception:
                pass

        data = self._read_shp_to_geojson(src_path, out_path)
        if not data:
            data = self._generate_fallback_districts()
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

        self._cache["districts"] = data
        return data

    def get_wards(self):
        if "wards" in self._cache:
            return self._cache["wards"]
            
        out_path = os.path.join(DATA_DIR, "wards.geojson")
        admin_base = r"F:\MTN - Main Desktop\Masters GIS  - Brandon Comp Science\Practical Assignment 5 (Fire Density)\data\extracted"
        src_path = os.path.join(admin_base, "zwe_admin3.shp")
        
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache["wards"] = data
                    return data
            except Exception:
                pass

        data = self._read_shp_to_geojson(src_path, out_path)
        if not data:
            data = self._generate_fallback_wards()
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

        self._cache["wards"] = data
        return data

    def get_protected_areas(self):
        if "protected_areas" in self._cache:
            return self._cache["protected_areas"]
            
        out_path = os.path.join(DATA_DIR, "protected_areas.geojson")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache["protected_areas"] = data
                    return data
            except Exception:
                pass
        src_path = r"F:\MTN - Main Desktop\Noma MAsters - GIS assignment\protected Areas.shp"
        fallback = self._generate_fallback_protected_areas()
        
        data = self._read_shp_to_geojson(src_path, out_path) or {"features": []}
        
        names = set()
        merged_features = []
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            name = props.get("NAME") or props.get("PARK_NAME") or props.get("Name") or "Protected Area"
            props["PARK_NAME"] = name
            props["LEGAL_STATUS"] = props.get("STATUS") or "Gazetted National Park / Wildlife Sanctuary"
            props["CATEGORY"] = props.get("DESIG") or "ZimParks IUCN Protected Area"
            props["ENVIRONMENTAL_RESTRICTION"] = "Mining & Commercial Extraction Prohibited (EMA / ZimParks)"
            props["COMPLIANCE_CODE"] = "EMA-ZIMPARKS-RESTRICTED"
            names.add(name.lower())
            merged_features.append(feat)
            
        for feat in fallback["features"]:
            p_name = feat["properties"]["PARK_NAME"].lower()
            if not any(n in p_name or p_name in n for n in names):
                merged_features.append(feat)
                
        result = {"type": "FeatureCollection", "features": merged_features}
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f)
        except Exception:
            pass

        self._cache["protected_areas"] = result
        return result

    # ─────────────────────────────────────────────
    # RIVERS
    # ─────────────────────────────────────────────
    def get_rivers(self):
        """Return Zimbabwe river network GeoJSON (merged ZimbabweRivers + 250k national lines)."""
        if "rivers" in self._cache:
            return self._cache["rivers"]

        out_path = os.path.join(DATA_DIR, "rivers.geojson")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache["rivers"] = data
                    return data
            except Exception:
                pass

        # Zimbabwe bounding box (lon_min, lat_min, lon_max, lat_max)
        ZW_BBOX = (25.2, -22.5, 33.1, -15.5)
        features = []

        # --- Primary: ZimbabweRivers (global dataset filtered to Zimbabwe) ---
        src1 = r"F:\Datasets\DATA_SETS\Rivers - Zimbabwe (my codes)\ZimbabweRivers.shp"
        try:
            import shapefile
            sf = shapefile.Reader(src1)
            flds = [f[0] for f in sf.fields[1:]]
            for sr in sf.shapeRecords():
                geom = sr.shape.__geo_interface__
                coords = geom.get("coordinates", [])
                # Quick bbox filter: check first coordinate
                if coords and isinstance(coords[0], (list, tuple)):
                    pt = coords[0] if not isinstance(coords[0][0], (list, tuple)) else coords[0][0]
                    if not (ZW_BBOX[0] <= pt[0] <= ZW_BBOX[2] and ZW_BBOX[1] <= pt[1] <= ZW_BBOX[3]):
                        continue
                props = dict(zip(flds, sr.record))
                clean = {}
                for k, v in props.items():
                    if isinstance(v, bytes):
                        clean[k] = v.decode("utf-8", errors="ignore")
                    elif isinstance(v, (int, float, str, bool)) or v is None:
                        clean[k] = v
                    else:
                        clean[k] = str(v)
                # Friendly display properties
                clean["RIVER_NAME"] = clean.get("BAS_NAME") or "Unnamed River"
                clean["ORDER"] = clean.get("RIV_ORD", "")
                clean["DISCHARGE_CMS"] = clean.get("DIS_AV_CMS", "")
                clean["UPLAND_KM2"] = clean.get("UPLAND_SKM", "")
                clean["LENGTH_KM"] = round(clean.get("LENGTH_KM", 0) or 0, 2)
                features.append({"type": "Feature", "properties": clean, "geometry": geom})
        except Exception as e:
            logger.warning(f"ZimbabweRivers load error: {e}")

        # --- Secondary: 250k named river lines (already clipped to Zimbabwe) ---
        src2 = r"F:\Datasets\DATA_SETS\GIS datasets- latest\Hydrology\Rivers\zwe_riverline_250k_dsg.shp"
        try:
            import shapefile as sf2mod
            sf2 = sf2mod.Reader(src2)
            flds2 = [f[0] for f in sf2.fields[1:]]
            for sr in sf2.shapeRecords():
                geom = sr.shape.__geo_interface__
                props = dict(zip(flds2, sr.record))
                clean = {}
                for k, v in props.items():
                    clean[k] = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else v
                clean["RIVER_NAME"] = clean.get("PRIMARY", "River")
                clean["SOURCE"] = "ZWE-250K"
                features.append({"type": "Feature", "properties": clean, "geometry": geom})
        except Exception as e:
            logger.warning(f"ZWE 250k rivers load error: {e}")

        fc = {"type": "FeatureCollection", "features": features}
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(fc, f)
        except Exception as e:
            logger.warning(f"Could not save rivers GeoJSON: {e}")

        self._cache["rivers"] = fc
        logger.info(f"Rivers: {len(features)} features loaded")
        return fc

    # ─────────────────────────────────────────────
    # SOIL (FAO World Soil Map – Zimbabwe clip)
    # ─────────────────────────────────────────────
    # FAO dominant soil code → readable name + mining relevance
    SOIL_LABELS = {
        "Af": "Ferralols (Af) — Deeply weathered laterite; high Al/Fe oxides",
        "Ao": "Orthic Acrisols (Ao) — Leached savanna soils; kaolinite dominant",
        "Bh": "Humic Cambisols (Bh) — Brown forest soils; moderate fertility",
        "Fh": "Humic Ferralsols (Fh) — Red clay laterite; bauxite potential",
        "Fo": "Orthic Ferralsols (Fo) — Classic Zimbabwe red soils; gold pathfinder",
        "Gh": "Humic Gleysols (Gh) — Wetland / dambo soils; alluvial gold",
        "Go": "Orthic Gleysols (Go) — Alluvial floodplain soils",
        "I":  "Lithosols (I) — Shallow rocky soils; basement outcrop indicator",
        "Je": "Eutric Fluvisols (Je) — River alluvium; placer mineral potential",
        "Lc": "Chromic Luvisols (Lc) — Chrome‑rich clay; chrome/PGM pathfinder",
        "Lo": "Orthic Luvisols (Lo) — Moderate fertility clay loam",
        "Nd": "Dystric Nitosols (Nd) — Deep red clayey; mafic parent material",
        "Ne": "Eutric Nitosols (Ne) — Productive red soils on mafic rocks",
        "Qc": "Calcaric Arenosols (Qc) — Sandy calcareous; limestone indicator",
        "Re": "Eutric Regosols (Re) — Weakly developed; active erosion zone",
        "Rx": "Rock Outcrops / Lithosols (Rx) — Exposed basement; no soil",
        "Th": "Humic Andosols (Th) — Volcanic ash soils (rare in Zimbabwe)",
        "Ve": "Eutric Vertisols (Ve) — Cracking black cotton soils; vlei zones",
        "Vp": "Pellic Vertisols (Vp) — Heavy clay; dambo / Lowveld vlei",
        "Vc": "Chromic Vertisols (Vc) — Dark Cr‑rich clay; ultramafic signal",
        "Xh": "Haplic Xerosols (Xh) — Semi-arid light soils; Lowveld",
        "Yh": "Haplic Yermosols (Yh) — Arid desert-margin soils",
        "Zg": "Gleyic Solonchaks (Zg) — Saline wetland soils",
    }

    def get_soil(self):
        """Return Zimbabwe soil GeoJSON clipped from FAO World Soil Map (DSMW)."""
        if "soil" in self._cache:
            return self._cache["soil"]

        out_path = os.path.join(DATA_DIR, "soil.geojson")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache["soil"] = data
                    return data
            except Exception:
                pass

        src = r"F:\Datasets\DATA_SETS\World Soil Data\DSMW.shp"
        ZW_BBOX = (25.2, -22.5, 33.1, -15.5)
        features = []

        try:
            import shapefile
            from shapely.geometry import shape as shp_shape, box as shp_box, mapping
            from shapely.ops import unary_union

            zw_box = shp_box(*ZW_BBOX)
            sf = shapefile.Reader(src)
            flds = [f[0] for f in sf.fields[1:]]

            for sr in sf.shapeRecords():
                props = dict(zip(flds, sr.record))
                country = (props.get("COUNTRY") or "").strip().upper()
                # Keep Zimbabwe records OR records whose geometry intersects ZW bbox
                if country not in ("ZIMBABWE", "ZWE", ""):
                    continue
                try:
                    geom_obj = shp_shape(sr.shape.__geo_interface__)
                    if not geom_obj.is_valid:
                        geom_obj = geom_obj.buffer(0)
                    if not geom_obj.intersects(zw_box):
                        continue
                    clipped = geom_obj.intersection(zw_box)
                    if clipped.is_empty:
                        continue
                    geom = mapping(clipped)
                except Exception:
                    continue

                clean = {}
                for k, v in props.items():
                    clean[k] = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else v

                dom = (clean.get("DOMSOI") or "").strip()
                fao = (clean.get("FAOSOIL") or "").strip()
                clean["SOIL_CODE"] = dom
                clean["FAO_UNIT"] = fao
                # Lookup readable label; fall back to prefix match
                label = self.SOIL_LABELS.get(dom)
                if not label:
                    for prefix, lbl in self.SOIL_LABELS.items():
                        if dom.startswith(prefix):
                            label = lbl
                            break
                clean["SOIL_NAME"] = label or f"FAO Soil Unit: {fao or dom}"
                clean["AREA_KM2"] = round(clean.get("SQKM", 0) or 0, 1)
                clean["PHASE"] = " / ".join(filter(None, [clean.get("PHASE1",""), clean.get("PHASE2","")]))
                features.append({"type": "Feature", "properties": clean, "geometry": geom})

        except Exception as e:
            logger.error(f"Soil data load error: {e}")

        fc = {"type": "FeatureCollection", "features": features}
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(fc, f)
        except Exception as e:
            logger.warning(f"Could not save soil GeoJSON: {e}")

        self._cache["soil"] = fc
        logger.info(f"Soil: {len(features)} features loaded for Zimbabwe")
        return fc

    # ─────────────────────────────────────────────
    # GEOLOGY (Africa Geology Map – Zimbabwe clip)
    # ─────────────────────────────────────────────
    # GLG codes from the FAO/BGS Africa geology layer
    GEOLOGY_LABELS = {
        "SEA":   ("Ocean / Sea", "#1a6b9a"),
        "Ar":    ("Archaean Basement (Granite-Greenstone)", "#8B4513"),
        "Pr":    ("Proterozoic Metamorphic / Gneiss", "#CD853F"),
        "Pa":    ("Palaeozoic Sedimentary (Karoo)", "#DAA520"),
        "Me":    ("Mesozoic Sedimentary", "#DEB887"),
        "Ce":    ("Cenozoic / Quaternary Sediments", "#F4A460"),
        "Cv":    ("Cenozoic Volcanic", "#FF6347"),
        "Pv":    ("Proterozoic Volcanic / Mafic", "#A0522D"),
        "Av":    ("Archaean Volcanic (Greenstone Belt)", "#556B2F"),
        "Ai":    ("Archaean Intrusive (Granites)", "#8FBC8F"),
        "Pi":    ("Proterozoic Intrusive / Layered Mafic", "#2E8B57"),
        "Ci":    ("Cenozoic Intrusive", "#FF8C00"),
        "Pu":    ("Proterozoic Undivided", "#B8860B"),
        "Au":    ("Archaean Undivided", "#996633"),
        "Mu":    ("Mixed / Undivided Metamorphic", "#708090"),
        "Qu":    ("Quaternary Alluvium / Colluvium", "#F5DEB3"),
        "Gl":    ("Glacial Deposits", "#ADD8E6"),
        "La":    ("Lakes / Water Bodies", "#4169E1"),
        "Lv":    ("Lava / Recent Volcanic", "#DC143C"),
        "Ka":    ("Karoo System (Coal-bearing Sediments)", "#808000"),
    }

    # Default color palette for unknown codes
    _GEO_PALETTE = [
        "#e74c3c","#e67e22","#f1c40f","#2ecc71","#1abc9c",
        "#3498db","#9b59b6","#34495e","#e91e63","#00bcd4",
    ]

    def get_geology(self):
        """Return Zimbabwe geology GeoJSON clipped from Africa geology shapefile."""
        if "geology" in self._cache:
            return self._cache["geology"]

        out_path = os.path.join(DATA_DIR, "geology.geojson")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache["geology"] = data
                    return data
            except Exception:
                pass

        src = r"F:\Datasets\DATA_SETS\Geology map - Africa\geo7_2ag.shp"
        ZW_BBOX = (25.2, -22.5, 33.1, -15.5)
        features = []
        code_index = 0
        code_colors = {}

        try:
            import shapefile
            from shapely.geometry import shape as shp_shape, box as shp_box, mapping

            zw_box = shp_box(*ZW_BBOX)
            sf = shapefile.Reader(src)
            flds = [f[0] for f in sf.fields[1:]]

            for sr in sf.shapeRecords():
                try:
                    geom_obj = shp_shape(sr.shape.__geo_interface__)
                    if not geom_obj.is_valid:
                        geom_obj = geom_obj.buffer(0)
                    if not geom_obj.intersects(zw_box):
                        continue
                    clipped = geom_obj.intersection(zw_box)
                    if clipped.is_empty:
                        continue
                    geom = mapping(clipped)
                except Exception:
                    continue

                props = dict(zip(flds, sr.record))
                clean = {}
                for k, v in props.items():
                    clean[k] = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else v

                glg = (clean.get("GLG") or "U").strip()
                if glg == "SEA":
                    continue  # Skip ocean polygons

                label_tuple = self.GEOLOGY_LABELS.get(glg)
                if label_tuple:
                    label, color = label_tuple
                else:
                    # Prefix-match
                    label, color = None, None
                    for prefix, (lbl, col) in self.GEOLOGY_LABELS.items():
                        if glg.startswith(prefix):
                            label, color = lbl, col
                            break
                    if not label:
                        label = f"Geological Unit: {glg}"
                    if not color:
                        if glg not in code_colors:
                            code_colors[glg] = self._GEO_PALETTE[code_index % len(self._GEO_PALETTE)]
                            code_index += 1
                        color = code_colors[glg]

                clean["GEO_CODE"] = glg
                clean["GEO_NAME"] = label
                clean["GEO_COLOR"] = color
                features.append({"type": "Feature", "properties": clean, "geometry": geom})

        except Exception as e:
            logger.error(f"Geology data load error: {e}")

        fc = {"type": "FeatureCollection", "features": features}
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(fc, f)
        except Exception as e:
            logger.warning(f"Could not save geology GeoJSON: {e}")

        self._cache["geology"] = fc
        logger.info(f"Geology: {len(features)} features loaded for Zimbabwe")
        return fc

    # Fallback GeoJSON generators representing official Zimbabwean jurisdictions
    def _generate_fallback_provinces(self):
        provinces = [
            {"name": "Midlands", "capital": "Gweru", "minerals": "Chrome, Gold, Platinum, Iron", "center": [-19.0, 29.8]},
            {"name": "Mashonaland West", "capital": "Chinhoyi", "minerals": "Platinum, Gold, Copper, Chrome", "center": [-17.5, 29.8]},
            {"name": "Mashonaland Central", "capital": "Bindura", "minerals": "Nickel, Gold, Lithium", "center": [-16.8, 31.2]},
            {"name": "Mashonaland East", "capital": "Marondera", "minerals": "Lithium, Granite, Gold", "center": [-18.2, 31.8]},
            {"name": "Matabeleland South", "capital": "Gwanda", "minerals": "Gold, Lithium, Limestone", "center": [-21.2, 29.0]},
            {"name": "Matabeleland North", "capital": "Lupane", "minerals": "Coal, Methane, Gold", "center": [-18.8, 27.8]},
            {"name": "Manicaland", "capital": "Mutare", "minerals": "Diamonds, Gold, Phosphate", "center": [-19.0, 32.4]},
            {"name": "Masvingo", "capital": "Masvingo", "minerals": "Lithium, Gold, Iron", "center": [-20.5, 31.2]},
            {"name": "Harare", "capital": "Harare Metropolitan", "minerals": "Refining, Commerce, ZIMRA", "center": [-17.82, 31.05]},
            {"name": "Bulawayo", "capital": "Bulawayo Metropolitan", "minerals": "Industrial Hub, Mining Engineering (NUST)", "center": [-20.15, 28.58]},
        ]
        features = []
        for p in provinces:
            c_lat, c_lng = p["center"]
            d = 0.85 if p["name"] not in ["Harare", "Bulawayo"] else 0.2
            poly = [
                [c_lng - d, c_lat - d],
                [c_lng + d, c_lat - d],
                [c_lng + d, c_lat + d],
                [c_lng - d, c_lat + d],
                [c_lng - d, c_lat - d]
            ]
            features.append({
                "type": "Feature",
                "properties": {
                    "PROVINCE": p["name"],
                    "CAPITAL": p["capital"],
                    "PRIMARY_MINERALS": p["minerals"],
                    "STATUS": "Gazetted Provincial Administration"
                },
                "geometry": {"type": "Polygon", "coordinates": [poly]}
            })
        return {"type": "FeatureCollection", "features": features}

    def _generate_fallback_districts(self):
        districts = [
            {"name": "Shurugwi", "province": "Midlands", "mineral": "Podiform Chromite & Gold", "center": [-19.67, 30.00]},
            {"name": "Kadoma", "province": "Mashonaland West", "mineral": "Archaean Gold Veins", "center": [-18.33, 29.91]},
            {"name": "Zvishavane", "province": "Midlands", "mineral": "Asbestos, Platinum, Chrome", "center": [-20.33, 30.06]},
            {"name": "Kwekwe", "province": "Midlands", "mineral": "Refractory Gold & Iron", "center": [-18.92, 29.81]},
            {"name": "Chegutu", "province": "Mashonaland West", "mineral": "Great Dyke Hartley PGMs", "center": [-18.13, 30.14]},
            {"name": "Bikita", "province": "Masvingo", "mineral": "Spodumene & Petalite Lithium", "center": [-19.95, 31.43]},
            {"name": "Gwanda", "province": "Matabeleland South", "mineral": "Greenstone Shear Gold", "center": [-20.93, 29.00]},
            {"name": "Bindura", "province": "Mashonaland Central", "mineral": "Nickel Sulphide (Trojan)", "center": [-17.30, 31.33]},
            {"name": "Goromonzi", "province": "Mashonaland East", "mineral": "Arcadia Lithium Hub", "center": [-17.80, 31.38]},
            {"name": "Binga", "province": "Matabeleland North", "mineral": "Coal, Fishery, Terra Drought ML", "center": [-17.62, 27.34]}
        ]
        features = []
        for d in districts:
            c_lat, c_lng = d["center"]
            poly = [
                [c_lng - 0.28, c_lat - 0.28],
                [c_lng + 0.28, c_lat - 0.28],
                [c_lng + 0.28, c_lat + 0.28],
                [c_lng - 0.28, c_lat + 0.28],
                [c_lng - 0.28, c_lat - 0.28]
            ]
            features.append({
                "type": "Feature",
                "properties": {
                    "DISTRICT": d["name"],
                    "PROVINCE": d["province"],
                    "MINING_FOCUS": d["mineral"],
                    "MINING_CADASTRE": f"Office of {d['name']} Mining Commissioner"
                },
                "geometry": {"type": "Polygon", "coordinates": [poly]}
            })
        return {"type": "FeatureCollection", "features": features}

    def _generate_fallback_wards(self):
        wards = [
            {"ward": "Ward 3", "district": "Shurugwi", "zone": "Selukwe Peak Chromite Belt", "center": [-19.65, 29.98]},
            {"ward": "Ward 7", "district": "Shurugwi", "zone": "Railway Block Underground", "center": [-19.70, 30.04]},
            {"ward": "Ward 12", "district": "Kadoma", "zone": "Claw Dam Artisanal Gold", "center": [-18.31, 29.88]},
            {"ward": "Ward 15", "district": "Kadoma", "zone": "Patchway Quartz Reef", "center": [-18.36, 29.94]},
            {"ward": "Ward 4", "district": "Bikita", "zone": "Bikita Minerals Pegmatite", "center": [-19.93, 31.41]},
            {"ward": "Ward 9", "district": "Bikita", "zone": "Spodumene Tailings & Washing", "center": [-19.97, 31.45]},
            {"ward": "Ward 2", "district": "Chegutu", "zone": "Hartley Complex PGM Open Pit", "center": [-18.11, 30.12]},
            {"ward": "Ward 8", "district": "Gwanda", "zone": "Colleen Bawn ASM Corridor", "center": [-20.91, 28.98]},
            {"ward": "Ward 1", "district": "Zvishavane", "zone": "Mimosa PGM Adit Zone", "center": [-20.31, 30.04]},
            {"ward": "Ward 6", "district": "Bindura", "zone": "Trojan Nickel Secondary Claims", "center": [-17.28, 31.31]}
        ]
        features = []
        for w in wards:
            c_lat, c_lng = w["center"]
            poly = [
                [c_lng - 0.08, c_lat - 0.08],
                [c_lng + 0.08, c_lat - 0.08],
                [c_lng + 0.08, c_lat + 0.08],
                [c_lng - 0.08, c_lat + 0.08],
                [c_lng - 0.08, c_lat - 0.08]
            ]
            features.append({
                "type": "Feature",
                "properties": {
                    "WARD": w["ward"],
                    "DISTRICT": w["district"],
                    "MINING_ZONE": w["zone"],
                    "STATUS": "Active ASM & Commercial Ward"
                },
                "geometry": {"type": "Polygon", "coordinates": [poly]}
            })
        return {"type": "FeatureCollection", "features": features}

    def _generate_fallback_protected_areas(self):
        parks = [
            {
                "name": "Hwange National Park",
                "category": "National Park (IUCN II)",
                "area_km2": 14651,
                "status": "STRICT CONSERVATION — ZERO MINING PERMITTED",
                "threat": "Coal & Gas exploration strictly barred by Cabinet Directive",
                "center": [-19.0, 26.5],
                "d_lat": 0.8,
                "d_lng": 1.1
            },
            {
                "name": "Mana Pools National Park & Sapi Safari Area",
                "category": "UNESCO World Heritage & RAMSAR Site",
                "area_km2": 2196,
                "status": "WORLD HERITAGE — ZERO MINING PERMITTED",
                "threat": "Zambezi alluvial conservation corridor",
                "center": [-15.8, 29.4],
                "d_lat": 0.35,
                "d_lng": 0.55
            },
            {
                "name": "Matobo Hills National Park",
                "category": "UNESCO World Heritage & Cultural Landscape",
                "area_km2": 424,
                "status": "SACRED CULTURAL & ECOLOGICAL RESERVE",
                "threat": "Granite quarrying & prospecting prohibited within 15km buffer",
                "center": [-20.55, 28.50],
                "d_lat": 0.22,
                "d_lng": 0.28
            },
            {
                "name": "Gonarezhou National Park",
                "category": "National Park & Great Limpopo Transfrontier",
                "area_km2": 5053,
                "status": "TRANSFRONTIER CONSERVATION AREA",
                "threat": "Strict biodiversity corridor — Mining exploration banned",
                "center": [-21.7, 31.8],
                "d_lat": 0.55,
                "d_lng": 0.70
            },
            {
                "name": "Matusadona National Park",
                "category": "National Park (Lake Kariba Shoreline)",
                "area_km2": 1407,
                "status": "NATIONAL PARK & WATER BASIN SANCTUARY",
                "threat": "Kariba catchment protection",
                "center": [-16.9, 28.5],
                "d_lat": 0.32,
                "d_lng": 0.40
            },
            {
                "name": "Chizarira National Park",
                "category": "National Park & Escarpment Wilderness",
                "area_km2": 2000,
                "status": "ESCARPMENT WILDERNESS RESERVE",
                "threat": "Zambezi escarpment protected wildlife habitat",
                "center": [-17.6, 27.9],
                "d_lat": 0.35,
                "d_lng": 0.45
            },
            {
                "name": "Sebakwe Recreational Park",
                "category": "Recreational Park & Dam Catchment",
                "area_km2": 260,
                "status": "WATER RESOURCE & LEISURE SANCTUARY",
                "threat": "Kwekwe / Midlands gold tailings discharge buffer",
                "center": [-19.0, 30.1],
                "d_lat": 0.15,
                "d_lng": 0.18
            },
            {
                "name": "Mafungabusi Forest Reserve",
                "category": "State Forest Reserve (Forestry Commission)",
                "area_km2": 820,
                "status": "GAZETTED INDIGENOUS HARDWOOD FOREST",
                "threat": "Timber & water catchment — Illegal gold panning strictly monitored",
                "center": [-18.2, 28.8],
                "d_lat": 0.25,
                "d_lng": 0.30
            },
            {
                "name": "Chimanimani National Park",
                "category": "National Park & Mountain Biosphere",
                "area_km2": 171,
                "status": "MOUNTAIN WATER TOWER BIOSPHERE",
                "threat": "Artisanal gold panning prohibited by ZimParks & EMA",
                "center": [-19.8, 33.0],
                "d_lat": 0.20,
                "d_lng": 0.20
            }
        ]
        features = []
        for p in parks:
            c_lat, c_lng = p["center"]
            d_lat = p["d_lat"]
            d_lng = p["d_lng"]
            poly = [
                [c_lng - d_lng, c_lat - d_lat],
                [c_lng + d_lng, c_lat - d_lat],
                [c_lng + d_lng, c_lat + d_lat],
                [c_lng - d_lng, c_lat + d_lat],
                [c_lng - d_lng, c_lat - d_lat]
            ]
            features.append({
                "type": "Feature",
                "properties": {
                    "PARK_NAME": p["name"],
                    "CATEGORY": p["category"],
                    "AREA_SQ_KM": p["area_km2"],
                    "LEGAL_STATUS": p["status"],
                    "ENVIRONMENTAL_RESTRICTION": p["threat"],
                    "COMPLIANCE_CODE": "EMA-ZIMPARKS-PROHIBITED"
                },
                "geometry": {"type": "Polygon", "coordinates": [poly]}
            })
        return {"type": "FeatureCollection", "features": features}

boundary_service = BoundaryService()
