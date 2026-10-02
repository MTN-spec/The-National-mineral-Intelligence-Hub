import os
import json
import shapefile
from shapely.geometry import shape, mapping
from pyproj import Transformer

# Output directory for GeoJSON
OUT_DIR = os.path.join(os.path.dirname(__file__), "src", "dashboard", "data")
os.makedirs(OUT_DIR, exist_ok=True)

def shp_to_geojson(shp_path, out_path, is_utm_or_local=False, from_epsg=None):
    if not os.path.exists(shp_path):
        print(f"File not found: {shp_path}")
        return False
        
    print(f"Converting {shp_path} -> {out_path}...")
    sf = shapefile.Reader(shp_path)
    fields = [f[0] for f in sf.fields[1:]]
    
    transformer = None
    if from_epsg:
        transformer = Transformer.from_crs(from_epsg, "EPSG:4326", always_xy=True)
    
    features = []
    for shape_rec in sf.shapeRecords():
        geom = shape_rec.shape.__geo_interface__
        props = dict(zip(fields, shape_rec.record))
        
        # Clean properties
        clean_props = {}
        for k, v in props.items():
            if isinstance(v, bytes):
                clean_props[k] = v.decode('utf-8', errors='ignore')
            elif isinstance(v, (int, float, str, bool)) or v is None:
                clean_props[k] = v
            else:
                clean_props[k] = str(v)
                
        # Reproject coordinates if needed
        if transformer:
            geom_obj = shape(geom)
            # Check if geometry coordinates are projected (> 1000)
            bounds = geom_obj.bounds
            if bounds[0] > 180 or bounds[1] > 90 or bounds[0] < -180 or bounds[1] < -90:
                from shapely.ops import transform
                reprojected = transform(transformer.transform, geom_obj)
                geom = mapping(reprojected)
        else:
            geom_obj = shape(geom)
            bounds = geom_obj.bounds
            # Auto-detect UTM 35S / 36S if coordinates are large (e.g. 200,000 - 8,000,000)
            if bounds[0] > 180 or bounds[1] < -100 or bounds[0] < -180:
                # Zimbabwe is predominantly UTM Zone 35S (EPSG:32735) or 36S (EPSG:32736) or Arc1950 (EPSG:20935/20936)
                for test_epsg in ["EPSG:32735", "EPSG:32736", "EPSG:20935", "EPSG:20936"]:
                    try:
                        trans = Transformer.from_crs(test_epsg, "EPSG:4326", always_xy=True)
                        from shapely.ops import transform
                        reproj = transform(trans.transform, geom_obj)
                        b = reproj.bounds
                        # Zimbabwe bbox roughly: lat -22.5 to -15.5, lon 25.0 to 33.2
                        if 24.0 <= b[0] <= 34.0 and -23.0 <= b[1] <= -15.0:
                            geom = mapping(reproj)
                            break
                    except:
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
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fc, f)
        
    print(f"Saved {len(features)} features to {out_path} ({os.path.getsize(out_path)} bytes)")
    return True

if __name__ == "__main__":
    # 1. Provinces
    p_src = r"F:\MTN - Main Desktop\AlertGRID\Provncial_Boundaries.shp"
    shp_to_geojson(p_src, os.path.join(OUT_DIR, "provinces.geojson"))
    
    # 2. Districts
    d_src = r"F:\MTN - Main Desktop\Thabani\Human Wildlife conflicts\Datasets\Districts.shp"
    shp_to_geojson(d_src, os.path.join(OUT_DIR, "districts.geojson"))
    
    # 3. Wards
    w_src = r"F:\MTN - Main Desktop\Thabani\Human Wildlife conflicts\Datasets\Wards.shp"
    shp_to_geojson(w_src, os.path.join(OUT_DIR, "wards.geojson"))
    
    # 4. Protected Areas / Parks
    pa_src = r"F:\MTN - Main Desktop\Noma MAsters - GIS assignment\protected Areas.shp"
    shp_to_geojson(pa_src, os.path.join(OUT_DIR, "protected_areas.geojson"))
