-- ============================================================================
-- THE NATIONAL MINERAL INTELLIGENCE HUB (NMIH) — CADASTRAL & GEOLOGICAL DATABASE
-- PostgreSQL 15+ / PostGIS 3+ Production Schema
-- Zimbabwe National Innovation Specification 2026 | MTN-SPEC (Pvt) Ltd
-- Standardized Geological, Spatial (Dual-CRS Arc 1950 / WGS 84), & Ownership Model
-- ============================================================================

-- 1. Enable PostGIS Spatial Extension & UUID Generator
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Enumerated Statutory & Geological Domain Types
DO $$ BEGIN
    CREATE TYPE claim_type_enum AS ENUM (
        'Precious Metals (Gold/Silver)',
        'Platinum Group Metals (PGM/MSZ)',
        'Strategic Minerals (Lithium/Rare Earths)',
        'Base Metals (Copper/Nickel/Cobalt)',
        'Chrome & Iron Ore (Podiform/Stratiform)',
        'Precious Stones (Diamond/Emerald)',
        'Special Grant (SG)',
        'Mining Lease (ML)',
        'Exclusive Prospecting Order (EPO)'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE tenure_status_enum AS ENUM (
        'Active Gazetted',
        'Application Pending',
        'Renewal In Progress',
        'Under Boundary Dispute',
        'Forfeited / Revoked',
        'Abandoned',
        'Draft Sandbox Simulation'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE deposit_genesis_enum AS ENUM (
        'Orogenic Lode Gold (Shear-Hosted)',
        'Stratiform Magmatic Layered PGM-Cr Reef (MSZ Type)',
        'LCT Granitic Pegmatite (Spodumene/Petalite)',
        'Podiform Ultramafic Chromite',
        'Banded Iron Formation (BIF Hosted Au/Fe)',
        'Volcanogenic Massive Sulfide (VMS)',
        'Carbonatite Rare Earth Complex',
        'Kimberlitic Pipe / Diamondiferous Placer',
        'Alluvial Secondary Placer'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE zimparks_clash_enum AS ENUM (
        'UNENCUMBERED_CLEARED',
        '500M_BUFFER_CAUTION',
        'CRITICAL_PROHIBITED_VIOLATION'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================================
-- TABLE 1: CLAIM OWNERS & CONCESSIONAIRES (Optimized for Fast SQL Lookups)
-- ============================================================================
CREATE TABLE IF NOT EXISTS claim_owners (
    owner_id VARCHAR(64) PRIMARY KEY,                         -- e.g. 'OWN-ZW-0081' or UUID
    entity_name VARCHAR(255) NOT NULL,                         -- Company, Syndicate, or Individual Name
    entity_type VARCHAR(64) NOT NULL DEFAULT 'Private Ltd',    -- 'Syndicate', 'Artisanal Cooperative', 'Private Ltd', 'State Enterprise', 'Foreign JV'
    registration_number VARCHAR(100) NOT NULL UNIQUE,          -- Company Reg / National ID / Cooperative Reg
    tax_tin_number VARCHAR(100),                               -- ZIMRA Tax Identification Number (BP No)
    contact_person VARCHAR(150),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(150),
    physical_address TEXT,
    province VARCHAR(100) NOT NULL,
    beneficial_ownership_pct NUMERIC(5,2) DEFAULT 100.00,       -- Local equity / Indigenization share %
    is_registered_syndicate BOOLEAN DEFAULT FALSE,
    ministry_mines_client_code VARCHAR(100),                   -- Cadastre portal client ID
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Fast Owner Lookups & SQL Queries
CREATE INDEX IF NOT EXISTS idx_owners_entity_name ON claim_owners (entity_name);
CREATE INDEX IF NOT EXISTS idx_owners_reg_no ON claim_owners (registration_number);
CREATE INDEX IF NOT EXISTS idx_owners_tax_tin ON claim_owners (tax_tin_number);
CREATE INDEX IF NOT EXISTS idx_owners_province ON claim_owners (province);

-- ============================================================================
-- TABLE 2: MASTER MINING CLAIMS (Primary Key: claim_id)
-- ============================================================================
CREATE TABLE IF NOT EXISTS mining_claims (
    -- Primary Key: Standardized Unique Claim Identifier
    claim_id VARCHAR(64) PRIMARY KEY,                          -- e.g. 'ZIM-GD-001', 'ZIM-HAR-2026-9081'
    
    -- Cadastral License & Registration
    license_number VARCHAR(100) NOT NULL UNIQUE,               -- Official Gazetted License (e.g. 'MC-HAR-202609081')
    claim_name VARCHAR(255) NOT NULL,                          -- e.g. 'Matanga Mine - Simba', 'Hartley PGM Complex'
    claim_type claim_type_enum NOT NULL,
    tenure_status tenure_status_enum NOT NULL DEFAULT 'Active Gazetted',
    
    -- Foreign Key Relation to Owner
    owner_id VARCHAR(64) NOT NULL REFERENCES claim_owners(owner_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    operator_name VARCHAR(255),                                -- Contract miner / Tribute Syndicate if different from owner
    
    -- Administrative Location
    country VARCHAR(32) DEFAULT 'Zimbabwe',
    province VARCHAR(100) NOT NULL,                            -- Midlands, Mashonaland West, Masvingo, etc.
    mining_district VARCHAR(100) NOT NULL,                     -- Shurugwi, Kadoma, Chegutu, Mberengwa, Gwanda
    ward_number VARCHAR(50),
    nearest_town VARCHAR(100),
    
    -- Statutory Dates
    application_date DATE,
    grant_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    last_renewal_date DATE,
    
    -- Cadastral Spatial Metrics
    area_hectares NUMERIC(12, 4) NOT NULL,                     -- Official Gazetted Hectares (e.g. 340.5000)
    area_acres NUMERIC(12, 4) GENERATED ALWAYS AS (area_hectares * 2.47105) STORED,
    perimeter_meters NUMERIC(12, 2) NOT NULL,
    beacons_count INTEGER NOT NULL CHECK (beacons_count >= 3),
    
    -- Coordinate Reference System (CRS) Standard
    projected_crs VARCHAR(32) NOT NULL DEFAULT 'EPSG:20936',   -- 'EPSG:20936' (Arc 1950 UTM 36S) or 'EPSG:20935' (UTM 35S)
    geographic_crs VARCHAR(32) NOT NULL DEFAULT 'EPSG:4326',   -- 'EPSG:4326' (WGS 84 Web Standard)
    
    -- Spatial Geometry Columns (PostGIS)
    -- 1. Web Display Geometry (WGS 84 / Lat-Lon)
    geom_wgs84 GEOMETRY(Polygon, 4326) NOT NULL,
    -- 2. Legal Metric Projected Geometry (Arc 1950 UTM 36S / 35S)
    geom_arc1950 GEOMETRY(Polygon, 20936),
    -- Centroid Location (Lat / Lng)
    centroid_lat NUMERIC(9, 6) NOT NULL,
    centroid_lng NUMERIC(9, 6) NOT NULL,
    
    -- Statutory Discovery Point (DP Beacon) — Primary Mineral Outcrop Peg
    has_discovery_point BOOLEAN DEFAULT TRUE,
    dp_geom_wgs84 GEOMETRY(Point, 4326),
    dp_easting_arc1950 NUMERIC(12, 2),                         -- Meters (e.g. 300450.00)
    dp_northing_arc1950 NUMERIC(12, 2),                        -- Meters (e.g. 7821500.00)
    dp_tie_beacon_id VARCHAR(32) DEFAULT 'B1',                 -- Tie anchor (normally Beacon B1)
    dp_tie_bearing_str VARCHAR(32),                            -- e.g. '042° 18'' 22"' (Whole Circle Bearing)
    dp_tie_bearing_deg NUMERIC(6, 2),                          -- 42.31 degrees
    dp_tie_distance_meters NUMERIC(10, 2),                     -- Ground distance from DP to Beacon 1
    
    -- Beacon Coordinates JSON Ledger
    -- Array of [{ peg: 'B1', easting: 300000, northing: 7820000, lat: -19.65, lng: 29.98 }, ...]
    beacons_ledger_json JSONB NOT NULL,
    
    -- Statutory & Environmental Compliance
    compliance_score INTEGER DEFAULT 90 CHECK (compliance_score BETWEEN 0 AND 100),
    ema_eia_certificate_no VARCHAR(100),                       -- Environmental Management Agency Certificate
    ema_license_expiry DATE,
    zimparks_status zimparks_clash_enum NOT NULL DEFAULT 'UNENCUMBERED_CLEARED',
    annual_inspection_fee_paid BOOLEAN DEFAULT TRUE,
    royalties_status VARCHAR(64) DEFAULT 'Up to Date',
    
    -- Operational Status
    production_stage VARCHAR(64) NOT NULL DEFAULT 'Active Extraction', -- 'Exploration', 'Development', 'Active Extraction', 'Care & Maintenance'
    monthly_tonnage_extracted NUMERIC(12, 2) DEFAULT 0.00,
    active_workforce INTEGER DEFAULT 0,
    processing_plant_type VARCHAR(100),                         -- 'CIL / CIP Plant', 'Gravity Concentrator', 'Heap Leach', 'Smelter Feed'
    
    -- System Audit Trail
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 3: GEOLOGICAL STANDARD SPECIFICATIONS (Linked 1:1 to Claim)
-- ============================================================================
CREATE TABLE IF NOT EXISTS claim_geology (
    claim_id VARCHAR(64) PRIMARY KEY REFERENCES mining_claims(claim_id) ON UPDATE CASCADE ON DELETE CASCADE,
    
    -- Commodities & Metallogeny
    primary_commodity VARCHAR(64) NOT NULL,                    -- 'Gold (Au)', 'Lithium (Li)', 'Platinum (Pt)', 'Chromite (Cr)'
    commodity_code VARCHAR(16) NOT NULL,                       -- 'Au', 'Li', 'PGE', 'Cr', 'Cu', 'Ni', 'C'
    secondary_commodities TEXT[],                              -- ARRAY['Silver', 'Copper', 'Cobalt', 'Nickel', 'Palladium']
    metallogenic_province VARCHAR(150) NOT NULL,               -- 'Great Dyke Layered Complex', 'Harare-Shamva Greenstone Belt', 'Midlands Greenstone Belt', 'Bikita Pegmatite Belt', 'Gwanda Greenstone Belt'
    subchamber_or_belt VARCHAR(150),                           -- 'Hartley Complex', 'Selukwe Subchamber', 'Wedza Subchamber', 'Musengezi Subchamber'
    
    -- Lithology & Stratigraphy
    geological_formation VARCHAR(200) NOT NULL,                -- 'Great Dyke Ultramafic Sequence', 'Sebakwian Group', 'Bulawayan Group', 'Shamvaian Group'
    geological_age_era VARCHAR(100) DEFAULT 'Archaean (>2.5 Ga)',
    host_rock VARCHAR(200) NOT NULL,                           -- 'Pyroxenite / Harzburgite', 'Banded Iron Formation (BIF)', 'Quartz-Carbonate Vein', 'Spodumene-Quartz Pegmatite', 'Serpentinite'
    hanging_wall_lithology VARCHAR(150),                       -- 'Gabbro-Norite', 'Basaltic Greenstone', 'Quartzite'
    foot_wall_lithology VARCHAR(150),                          -- 'Dunite', 'Felsic Tuff', 'Banded Ironstone'
    
    -- Genesis & Mineralization Style
    deposit_genesis deposit_genesis_enum NOT NULL,
    mineralization_style VARCHAR(200) NOT NULL,                -- 'Sulfide Disseminated Horizon (MSZ)', 'Hydrothermal Quartz Lode', 'Zoned LCT Lithium Pegmatite', 'Massive Seam Chromitite'
    primary_ore_minerals TEXT[],                               -- ARRAY['Sperrylite', 'Braggite', 'Chalcopyrite', 'Pentlandite', 'Spodumene', 'Petalite', 'Native Gold', 'Chromite']
    gangue_minerals TEXT[],                                    -- ARRAY['Quartz', 'Calcite', 'Pyrite', 'Arsenopyrite', 'Serpentine', 'Plagioclase']
    
    -- Structural Controls
    structural_controls VARCHAR(255) NOT NULL,                 -- 'Transverse Graben Shear Fault', 'Anticlinal Hinge Fold', 'Brittle-Ductile Shear Zone'
    fault_trend VARCHAR(50),                                   -- 'NNE-SSW 020°', 'ENE-WSW 070°'
    dip_angle_degrees NUMERIC(4, 1),                           -- Dip Angle in degrees (e.g. 14.5°, 65.0°)
    dip_direction VARCHAR(32),                                 -- 'East', 'SSE', 'Vertical'
    strike_length_meters NUMERIC(10, 2),                       -- Outcrop length along strike
    average_true_thickness_m NUMERIC(6, 2),                    -- Reef true thickness (e.g. 2.10 m for MSZ)
    depth_to_orebody_m NUMERIC(8, 2),                          -- Depth from surface (0.00 for open pits)
    
    -- Alteration Halo & Geochemistry
    alteration_style VARCHAR(200),                             -- 'Silicification, Carbonatization, Chloritization & Pyritization'
    weathering_profile_depth_m NUMERIC(6, 2),                  -- Oxide / Weathering zone depth
    gossan_indicator_present BOOLEAN DEFAULT FALSE,            -- Presence of Iron Oxide Gossan cap
    spectral_band_math_signature VARCHAR(200),                 -- 'Sentinel-2 SWIR1/SWIR2 (B11/B12 > 1.8)', 'B4/B2 Gossan Peak'
    
    -- JORC / SAMREC / NI 43-101 Resource & Reserve Estimates
    resource_compliance_code VARCHAR(32) DEFAULT 'JORC 2012 / SAMREC',
    estimated_resource_tonnage_mt NUMERIC(10, 3),              -- Million Tonnes (e.g. 14.500 Mt)
    average_ore_grade VARCHAR(100) NOT NULL,                   -- e.g. '3.85 g/t 4E (Pt+Pd+Rh+Au)', '1.65% Li2O', '5.20 g/t Au', '48.5% Cr2O3'
    cut_off_grade VARCHAR(100),                                -- e.g. '1.50 g/t Au', '0.60% Li2O'
    contained_metal_content VARCHAR(100),                      -- e.g. '1.79 Million Ounces 4E PGE', '239,250 tonnes LCE', '125,000 oz Au'
    resource_category VARCHAR(64) DEFAULT 'Measured & Indicated', -- 'Measured', 'Indicated', 'Inferred', 'Exploration Target'
    
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 4: DETAILED CADASTRAL BEACONS (1:N Relation to Claims)
-- ============================================================================
CREATE TABLE IF NOT EXISTS claim_beacons (
    beacon_pk UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id VARCHAR(64) NOT NULL REFERENCES mining_claims(claim_id) ON UPDATE CASCADE ON DELETE CASCADE,
    beacon_label VARCHAR(32) NOT NULL,                         -- 'B1', 'B2', 'B3', 'B4', 'DP'
    sequence_order INTEGER NOT NULL,                           -- 1, 2, 3, 4 ...
    is_discovery_point BOOLEAN DEFAULT FALSE,                  -- TRUE if this is the statutory DP
    
    -- Projected Coordinates (Arc 1950 UTM Zone 36S / 35S)
    easting_meters NUMERIC(12, 2) NOT NULL,                    -- Legal Metric X
    northing_meters NUMERIC(12, 2) NOT NULL,                   -- Legal Metric Y
    projected_crs VARCHAR(32) NOT NULL DEFAULT 'EPSG:20936',
    
    -- Geographic Coordinates (WGS 84)
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    geographic_crs VARCHAR(32) NOT NULL DEFAULT 'EPSG:4326',
    
    -- Physical Peg Description
    physical_marker_type VARCHAR(100) DEFAULT 'Standard Concrete Beacon with Iron Rod', -- 'Iron Peg with Cairn', 'Concrete Pillar', 'Painted Rock Cairn'
    elevation_meters NUMERIC(8, 2),
    surveyor_name VARCHAR(150),
    survey_date DATE,
    
    geom_wgs84 GEOMETRY(Point, 4326) NOT NULL,
    
    CONSTRAINT uq_claim_beacon UNIQUE (claim_id, beacon_label)
);

-- ============================================================================
-- HIGH-PERFORMANCE POSTGRESQL & POSTGIS INDEXES
-- ============================================================================
-- Spatial GiST Indexes (Lightning-fast spatial intersections, bounding box queries & distance scans)
CREATE INDEX IF NOT EXISTS idx_claims_geom_wgs84 ON mining_claims USING GIST (geom_wgs84);
CREATE INDEX IF NOT EXISTS idx_claims_geom_arc1950 ON mining_claims USING GIST (geom_arc1950);
CREATE INDEX IF NOT EXISTS idx_claims_dp_geom ON mining_claims USING GIST (dp_geom_wgs84);
CREATE INDEX IF NOT EXISTS idx_beacons_geom ON claim_beacons USING GIST (geom_wgs84);

-- Standard SQL B-Tree Indexes for Filtering, Grouping & Joins
CREATE INDEX IF NOT EXISTS idx_claims_owner_id ON mining_claims (owner_id);
CREATE INDEX IF NOT EXISTS idx_claims_license ON mining_claims (license_number);
CREATE INDEX IF NOT EXISTS idx_claims_name ON mining_claims (claim_name);
CREATE INDEX IF NOT EXISTS idx_claims_status ON mining_claims (tenure_status);
CREATE INDEX IF NOT EXISTS idx_claims_province ON mining_claims (province);
CREATE INDEX IF NOT EXISTS idx_claims_district ON mining_claims (mining_district);
CREATE INDEX IF NOT EXISTS idx_claims_area ON mining_claims (area_hectares);

CREATE INDEX IF NOT EXISTS idx_geology_commodity ON claim_geology (primary_commodity);
CREATE INDEX IF NOT EXISTS idx_geology_code ON claim_geology (commodity_code);
CREATE INDEX IF NOT EXISTS idx_geology_province ON claim_geology (metallogenic_province);
CREATE INDEX IF NOT EXISTS idx_geology_formation ON claim_geology (geological_formation);
CREATE INDEX IF NOT EXISTS idx_geology_genesis ON claim_geology (deposit_genesis);

-- ============================================================================
-- CONVENIENCE VIEWS FOR INSTANT SQL QUERIES & API ENDPOINTS
-- ============================================================================

-- View 1: Complete Master Claim Profile with Geological & Owner Details Joined
CREATE OR REPLACE VIEW v_mining_claims_master AS
SELECT 
    c.claim_id,
    c.license_number,
    c.claim_name,
    c.claim_type,
    c.tenure_status,
    c.production_stage,
    
    -- Owner Details
    o.entity_name AS owner_name,
    o.entity_type AS owner_type,
    o.registration_number AS owner_reg_no,
    o.tax_tin_number AS owner_tax_tin,
    o.contact_phone AS owner_phone,
    o.contact_email AS owner_email,
    o.beneficial_ownership_pct,
    c.operator_name,
    
    -- Administrative Location
    c.province,
    c.mining_district,
    c.ward_number,
    
    -- Cadastral Spatial Metrics
    c.area_hectares,
    c.area_acres,
    c.perimeter_meters,
    c.beacons_count,
    c.projected_crs,
    c.centroid_lat,
    c.centroid_lng,
    
    -- Discovery Point (DP) Statutory Data
    c.has_discovery_point,
    c.dp_easting_arc1950,
    c.dp_northing_arc1950,
    c.dp_tie_bearing_str AS dp_tie_bearing,
    c.dp_tie_distance_meters AS dp_tie_distance_m,
    
    -- Geological Standard Attributes
    g.primary_commodity,
    g.commodity_code,
    g.secondary_commodities,
    g.metallogenic_province,
    g.geological_formation,
    g.host_rock,
    g.deposit_genesis,
    g.mineralization_style,
    g.structural_controls,
    g.average_ore_grade,
    g.estimated_resource_tonnage_mt,
    g.contained_metal_content,
    g.resource_category,
    
    -- Statutory & Environmental Compliance
    c.compliance_score,
    c.ema_eia_certificate_no,
    c.zimparks_status,
    c.grant_date,
    c.expiry_date,
    
    -- GeoJSON Geometry strings ready for web frontend
    ST_AsGeoJSON(c.geom_wgs84)::json AS geometry_geojson,
    ST_AsGeoJSON(c.dp_geom_wgs84)::json AS dp_geometry_geojson
FROM mining_claims c
JOIN claim_owners o ON c.owner_id = o.owner_id
LEFT JOIN claim_geology g ON c.claim_id = g.claim_id;

-- View 2: Owner Portfolio Summary View
CREATE OR REPLACE VIEW v_owner_portfolios AS
SELECT 
    o.owner_id,
    o.entity_name,
    o.entity_type,
    o.registration_number,
    COUNT(c.claim_id) AS total_claims_held,
    ROUND(SUM(c.area_hectares), 2) AS total_hectares_held,
    ARRAY_AGG(DISTINCT g.primary_commodity) FILTER (WHERE g.primary_commodity IS NOT NULL) AS commodity_portfolio,
    ARRAY_AGG(DISTINCT c.mining_district) AS active_districts,
    ROUND(AVG(c.compliance_score), 1) AS avg_compliance_score
FROM claim_owners o
LEFT JOIN mining_claims c ON o.owner_id = c.owner_id
LEFT JOIN claim_geology g ON c.claim_id = g.claim_id
GROUP BY o.owner_id, o.entity_name, o.entity_type, o.registration_number;

