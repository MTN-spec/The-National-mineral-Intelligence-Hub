"""
Production PostgreSQL + PostGIS Database Layer for The National Mineral Intelligence Hub.
Handles connection pooling, spatial queries (ST_DWithin, ST_Contains, ST_Distance),
Dual-CRS projections (EPSG:4326 <-> EPSG:20936), borehole analytics, AI telemetry,
market snapshots, ore transit permits, and advisor audit logging.
"""
import os
import json
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, Json

logger = logging.getLogger("nmih.db")

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
_DB_POOL: Optional[pool.ThreadedConnectionPool] = None


def is_db_configured() -> bool:
    return bool(DATABASE_URL)


def init_db_pool() -> Optional[pool.ThreadedConnectionPool]:
    global _DB_POOL
    if not DATABASE_URL:
        return None
    if _DB_POOL is None:
        _DB_POOL = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL,
            cursor_factory=RealDictCursor,
        )
    return _DB_POOL


@contextmanager
def get_conn():
    p = init_db_pool()
    if p is None:
        raise RuntimeError("DATABASE_URL is not configured. Cannot connect to PostgreSQL/PostGIS.")
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def check_db_health() -> Dict[str, Any]:
    if not DATABASE_URL:
        return {"connected": False, "engine": "none", "reason": "DATABASE_URL not set"}
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version() AS pg_ver, PostGIS_Version() AS postgis_ver;")
                row = cur.fetchone()
                cur.execute("SELECT COUNT(*) AS cnt FROM boreholes;")
                bh_cnt = cur.fetchone()["cnt"]
                cur.execute("SELECT COUNT(*) AS cnt FROM mining_claims;")
                cl_cnt = cur.fetchone()["cnt"]
                return {
                    "connected": True,
                    "engine": "PostgreSQL + PostGIS",
                    "postgres_version": row["pg_ver"].split(",")[0],
                    "postgis_version": row["postgis_ver"],
                    "boreholes_count": bh_cnt,
                    "claims_count": cl_cnt,
                }
    except Exception as e:
        return {"connected": False, "engine": "PostgreSQL + PostGIS", "error": str(e)}


def query_concessions_from_db(filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    claim_id AS id,
                    license_number,
                    claim_name AS name,
                    claim_type::text AS claim_type,
                    tenure_status::text AS status,
                    production_stage,
                    owner_name AS owner,
                    province,
                    mining_district AS district,
                    area_hectares::float AS area_hectares,
                    centroid_lat::float AS lat,
                    centroid_lng::float AS lng,
                    primary_commodity AS mineral,
                    commodity_code,
                    host_rock,
                    geological_formation,
                    structural_controls,
                    average_ore_grade AS estimated_grade,
                    estimated_resource_tonnage_mt::float AS resource_tonnage_mt,
                    contained_metal_content,
                    compliance_score,
                    zimparks_status::text AS zimparks_status,
                    geometry_geojson
                FROM v_mining_claims_master
            """
            params = []
            if filter_status and filter_status != "all":
                sql += " WHERE LOWER(tenure_status::text) = LOWER(%s)"
                params.append(filter_status)
            sql += " ORDER BY claim_id;"
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["yield_rating"] = "High Yield" if (d.get("compliance_score") or 0) >= 85 else "Moderate"
                d["risk_level"] = "Low" if d.get("zimparks_status") == "UNENCUMBERED_CLEARED" else "Moderate"
                results.append(d)
            return results


def query_boreholes_geojson(domain: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    borehole_id AS id,
                    domain,
                    collar_elevation_m::float,
                    msz_depth_m::float,
                    msz_elevation_rl::float,
                    ore_state,
                    rock_competence,
                    dip::float,
                    bearing::float,
                    local_x::float,
                    local_y::float,
                    horizon,
                    pge_basket,
                    ST_X(geom) AS lng,
                    ST_Y(geom) AS lat
                FROM boreholes
            """
            params: List[Any] = []
            if domain:
                sql += " WHERE UPPER(domain) = UPPER(%s)"
                params.append(domain)
            sql += " ORDER BY borehole_id LIMIT %s;"
            params.append(limit)
            cur.execute(sql, params)
            features = []
            for r in cur.fetchall():
                features.append({
                    "type": "Feature",
                    "properties": {
                        "id": r["id"],
                        "domain": r["domain"],
                        "collar_elevation_m": r["collar_elevation_m"],
                        "msz_depth_m": r["msz_depth_m"],
                        "msz_elevation_rl": r["msz_elevation_rl"],
                        "ore_state": r["ore_state"],
                        "rock_competence": r["rock_competence"],
                        "dip": r["dip"],
                        "bearing": r["bearing"],
                        "local_x": r["local_x"],
                        "local_y": r["local_y"],
                        "horizon": r["horizon"],
                        "pge_basket": r["pge_basket"],
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [r["lng"], r["lat"]],
                    },
                })
            return {
                "type": "FeatureCollection",
                "name": "Mimosa_PGE_Drillhole_Database",
                "source": "PostgreSQL/PostGIS Live Query",
                "features": features,
            }


def analyze_spatial_target(lat: float, lng: float, radius_m: int = 2500) -> Dict[str, Any]:
    """
    Real PostGIS Spatial Analytics around a target coordinate (WGS84):
    - Counts boreholes within radius_m using geography distance
    - Computes mean MSZ elevation RL, depth, oxide vs sulphide %, structural competence %
    - Computes distance to nearest geological fault
    - Checks enclosing Great Dyke resource block
    - Projects coordinate to Arc 1950 UTM 36S (EPSG:20936) in PostGIS
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # 1. Dual-CRS projection in PostGIS
            cur.execute("""
                SELECT
                    ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 20936)) AS arc_easting,
                    ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 20936)) AS arc_northing;
            """, (lng, lat, lng, lat))
            crs_row = cur.fetchone()

            # 2. Borehole spatial aggregation within radius_m
            cur.execute("""
                SELECT
                    COUNT(*) AS borehole_count,
                    ROUND(AVG(msz_elevation_rl)::numeric, 2) AS avg_msz_rl_m,
                    ROUND(AVG(msz_depth_m)::numeric, 2) AS avg_msz_depth_m,
                    ROUND(MIN(msz_elevation_rl)::numeric, 2) AS min_msz_rl_m,
                    ROUND(MAX(msz_elevation_rl)::numeric, 2) AS max_msz_rl_m,
                    SUM(CASE WHEN ore_state = 'OXIDE' THEN 1 ELSE 0 END) AS oxide_count,
                    SUM(CASE WHEN ore_state = 'SULPHIDE' THEN 1 ELSE 0 END) AS sulphide_count,
                    SUM(CASE WHEN rock_competence = 'STRUC' THEN 1 ELSE 0 END) AS structural_fault_flags,
                    ARRAY_AGG(DISTINCT domain) FILTER (WHERE domain IS NOT NULL) AS sectors
                FROM boreholes
                WHERE ST_DWithin(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    %s
                );
            """, (lng, lat, radius_m))
            bh_stats = dict(cur.fetchone() or {})

            # 3. Distance to nearest mapped geological fault
            cur.execute("""
                SELECT
                    fault_name,
                    ROUND(ST_Distance(
                        geom::geography,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    )::numeric, 1) AS distance_m
                FROM geological_faults
                ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                LIMIT 1;
            """, (lng, lat, lng, lat))
            fault_row = dict(cur.fetchone() or {})

            # 4. Enclosing resource block
            cur.execute("""
                SELECT res_num_id, block_name, subchamber
                FROM resource_blocks
                WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                LIMIT 1;
            """, (lng, lat))
            block_row = dict(cur.fetchone() or {})

            return {
                "coordinates": {
                    "wgs84": {"lat": lat, "lng": lng},
                    "arc1950_utm36s": {
                        "easting": round(float(crs_row["arc_easting"]), 2) if crs_row else None,
                        "northing": round(float(crs_row["arc_northing"]), 2) if crs_row else None,
                    },
                },
                "search_radius_m": radius_m,
                "borehole_analytics": {
                    k: (float(v) if hasattr(v, "quantize") else v)
                    for k, v in bh_stats.items()
                },
                "nearest_fault": {
                    "name": fault_row.get("fault_name"),
                    "distance_m": float(fault_row["distance_m"]) if fault_row.get("distance_m") is not None else None,
                },
                "enclosing_resource_block": block_row or None,
            }


def get_latest_ai_telemetry() -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT telemetry_payload
                FROM ai_training_runs
                ORDER BY created_at DESC
                LIMIT 1;
            """)
            row = cur.fetchone()
            return row["telemetry_payload"] if row else None


def record_advisor_inquiry(
    target_name: str,
    lat: Optional[float],
    lng: Optional[float],
    question: str,
    spatial_context: Dict[str, Any],
    response_text: str,
    model_used: str,
) -> str:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO advisor_inquiries (
                    target_name, target_lat, target_lng, user_question,
                    spatial_context_json, advisor_response, model_used
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING inquiry_id::text;
            """, (
                target_name, lat, lng, question,
                Json(spatial_context), response_text, model_used,
            ))
            return cur.fetchone()["inquiry_id"]


def record_market_snapshot(commodities: List[Dict[str, Any]]) -> None:
    if not commodities:
        return
    with get_conn() as conn:
        with conn.cursor() as cur:
            for item in commodities:
                cur.execute("""
                    INSERT INTO market_price_snapshots (commodity_name, ticker, price_usd, change_pct, source)
                    VALUES (%s, %s, %s, %s, %s);
                """, (
                    item.get("name", "Unknown"),
                    item.get("ticker", "N/A"),
                    float(item.get("price", 0.0)),
                    float(item.get("change_pct", 0.0)),
                    item.get("source", "yfinance"),
                ))


def record_permit_to_db(permit: Dict[str, Any]) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ore_transit_permits (
                    permit_id, claim_id, mineral_type, tonnage_mt,
                    origin_district, destination_plant, transporter_reg,
                    hmac_signature, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (permit_id) DO NOTHING;
            """, (
                permit["permit_id"],
                permit.get("claim_id"),
                permit["mineral_type"],
                float(permit["tonnage_mt"]),
                permit["origin_district"],
                permit["destination_plant"],
                permit.get("transporter_reg", ""),
                permit["hmac_signature"],
                "VALID",
            ))
