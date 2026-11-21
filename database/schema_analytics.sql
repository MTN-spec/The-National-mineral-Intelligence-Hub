-- ============================================================================
-- THE NATIONAL MINERAL INTELLIGENCE HUB (NMIH) — ANALYTICS, BOREHOLES & AI DB
-- PostgreSQL 15+ / PostGIS 3+ Extension Schema (002)
-- Stores subsurface drillholes, structural faults, resource blocks,
-- AI training telemetry, market snapshots, permits, and client AI inquiries.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. SUBSURFACE BOREHOLES (3D Desurveyed Mimosa & National Drillholes)
CREATE TABLE IF NOT EXISTS boreholes (
    borehole_id VARCHAR(64) PRIMARY KEY,
    domain VARCHAR(64) NOT NULL,                          -- e.g. 'NH', 'SH', 'MSZ'
    collar_elevation_m NUMERIC(10, 3),
    msz_depth_m NUMERIC(10, 3),
    msz_elevation_rl NUMERIC(10, 3),
    ore_state VARCHAR(32) NOT NULL DEFAULT 'SULPHIDE',    -- 'OXIDE' or 'SULPHIDE'
    rock_competence VARCHAR(32) NOT NULL DEFAULT 'FRESH', -- 'STRUC' or 'FRESH'
    dip NUMERIC(6, 2) DEFAULT -90.0,
    bearing NUMERIC(6, 2) DEFAULT 0.0,
    local_x NUMERIC(14, 3),
    local_y NUMERIC(14, 3),
    horizon VARCHAR(128) DEFAULT 'Main Sulphide Zone (MSZ)',
    pge_basket TEXT DEFAULT 'Pt, Pd, Rh, Au, Ru, Ir, Os, Ni, Cu, Co',
    geom GEOMETRY(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_boreholes_geom ON boreholes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_boreholes_domain ON boreholes (domain);
CREATE INDEX IF NOT EXISTS idx_boreholes_ore_state ON boreholes (ore_state);

-- 2. GEOLOGICAL FAULTS & SHEAR ZONES
CREATE TABLE IF NOT EXISTS geological_faults (
    fault_id SERIAL PRIMARY KEY,
    fault_name VARCHAR(150),
    fault_type VARCHAR(100),
    properties_json JSONB DEFAULT '{}'::jsonb,
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_faults_geom ON geological_faults USING GIST (geom);

-- 3. RESOURCE BLOCKS (Great Dyke & National Mineral Blocks)
CREATE TABLE IF NOT EXISTS resource_blocks (
    block_id SERIAL PRIMARY KEY,
    res_num_id VARCHAR(64),
    block_name VARCHAR(200),
    subchamber VARCHAR(150),
    properties_json JSONB DEFAULT '{}'::jsonb,
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_resource_blocks_geom ON resource_blocks USING GIST (geom);

-- 4. AI DEEP LEARNING TRAINING TELEMETRY & MODEL RUNS
CREATE TABLE IF NOT EXISTS ai_training_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    model_name VARCHAR(150) NOT NULL,
    architecture VARCHAR(150) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'CONVERGED',
    epochs_total INTEGER NOT NULL,
    early_stop_epoch INTEGER NOT NULL,
    train_loss_final NUMERIC(10, 6),
    val_loss_final NUMERIC(10, 6),
    host_ram_used_gb NUMERIC(8, 2),
    host_ram_total_gb NUMERIC(8, 2),
    gpu_vram_used_gb NUMERIC(8, 2),
    gpu_vram_total_gb NUMERIC(8, 2),
    nvme_scratch_gb NUMERIC(8, 2),
    trainable_params BIGINT,
    inference_latency_ms NUMERIC(8, 2),
    telemetry_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. CLIENT GEOLOGICAL AI INQUIRIES & PROSPECTUS AUDIT LOG
CREATE TABLE IF NOT EXISTS advisor_inquiries (
    inquiry_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_name VARCHAR(255),
    target_lat NUMERIC(9, 6),
    target_lng NUMERIC(9, 6),
    user_question TEXT NOT NULL,
    spatial_context_json JSONB NOT NULL,
    advisor_response TEXT NOT NULL,
    model_used VARCHAR(100) DEFAULT 'postgis-rag-engine',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_inquiries_created ON advisor_inquiries (created_at DESC);

-- 6. LIVE MARKET PRICE SNAPSHOTS (yfinance Historical Audit)
CREATE TABLE IF NOT EXISTS market_price_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    commodity_name VARCHAR(64) NOT NULL,
    ticker VARCHAR(32) NOT NULL,
    price_usd NUMERIC(14, 4) NOT NULL,
    change_pct NUMERIC(8, 4),
    source VARCHAR(64) DEFAULT 'yfinance',
    recorded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_market_commodity_time ON market_price_snapshots (commodity_name, recorded_at DESC);

-- 7. ORE TRANSIT PERMITS LEDGER
CREATE TABLE IF NOT EXISTS ore_transit_permits (
    permit_id VARCHAR(64) PRIMARY KEY,
    claim_id VARCHAR(64),
    mineral_type VARCHAR(100) NOT NULL,
    tonnage_mt NUMERIC(12, 3) NOT NULL,
    origin_district VARCHAR(100) NOT NULL,
    destination_plant VARCHAR(150) NOT NULL,
    transporter_reg VARCHAR(64),
    hmac_signature VARCHAR(128) NOT NULL,
    status VARCHAR(32) DEFAULT 'VALID',
    issued_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
