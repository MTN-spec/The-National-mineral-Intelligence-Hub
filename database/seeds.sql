-- ============================================================================
-- THE NATIONAL MINERAL INTELLIGENCE HUB (NMIH) — SEED DATA
-- Zimbabwe Sovereign Mining Claims, Geology & Owner Ledger
-- Compliant with PostgreSQL 15+ / PostGIS Schema
-- ============================================================================

-- 1. SEED CLAIM OWNERS & SYNDICATES
INSERT INTO claim_owners (
    owner_id, entity_name, entity_type, registration_number, tax_tin_number, 
    contact_person, contact_phone, contact_email, physical_address, 
    province, beneficial_ownership_pct, is_registered_syndicate, ministry_mines_client_code
) VALUES 
(
    'OWN-ZW-001', 
    'ZIMASCO Artisanal Syndicate Limited', 
    'Syndicate', 
    'SYND-SHU-2021-0044', 
    'BP-2000881920', 
    'Kudzai Mpofu', 
    '+263 77 219 4410', 
    'operations@zimasco-syndicate.co.zw', 
    'Stand 14, Peak Mine Road, Shurugwi', 
    'Midlands', 
    100.00, 
    TRUE, 
    'MM-CL-8891'
),
(
    'OWN-ZW-002', 
    'Zimplats Hartley Joint Venture (Pvt) Ltd', 
    'Private Ltd', 
    'CO-CHE-1998-1092', 
    'BP-1000994411', 
    'Chipo Ndlovu', 
    '+263 71 288 3301', 
    'hartley.mining@zimplats.co.zw', 
    'Ngezi Mine Complex, Chegutu District', 
    'Mashonaland West', 
    51.00, 
    FALSE, 
    'MM-CL-1092'
),
(
    'OWN-ZW-003', 
    'Kadoma Artisanal Gold Miners Cooperative', 
    'Artisanal Cooperative', 
    'COOP-KAD-2019-082', 
    'BP-3000771239', 
    'Farai Mutasa', 
    '+263 73 345 6789', 
    'kadoma.miners@coop.co.zw', 
    'Office 4, Rimuka Commercial Centre, Kadoma', 
    'Mashonaland West', 
    100.00, 
    TRUE, 
    'MM-CL-0824'
),
(
    'OWN-ZW-004', 
    'Bikita Minerals Consortium (Pvt) Ltd', 
    'Private Ltd', 
    'CO-MAS-1961-0012', 
    'BP-1000552190', 
    'Tawanda Moyo', 
    '+263 77 455 1200', 
    'geology@bikitaminerals.co.zw', 
    'Bikita Pegmatite Mine, Fort Victoria Highway, Masvingo', 
    'Masvingo', 
    60.00, 
    FALSE, 
    'MM-CL-0012'
),
(
    'OWN-ZW-005', 
    'Matanga - Simba Mining Syndicate', 
    'Syndicate', 
    'SYND-MBE-2023-0199', 
    'BP-4000331908', 
    'Simbarashe Zhou', 
    '+263 78 512 8844', 
    'matanga.simba@mining.co.zw', 
    'Matanga Business Centre, Mberengwa East', 
    'Midlands', 
    100.00, 
    TRUE, 
    'MM-CL-0199'
),
(
    'OWN-ZW-006', 
    'Gwanda South Gold Syndicate', 
    'Syndicate', 
    'SYND-GWA-2020-0071', 
    'BP-3000118823', 
    'Dumisani Sibanda', 
    '+263 77 699 0012', 
    'gwanda.gold@syndicate.co.zw', 
    'Colleen Bawn Siding, Gwanda District', 
    'Matabeleland South', 
    100.00, 
    TRUE, 
    'MM-CL-0071'
)
ON CONFLICT (owner_id) DO NOTHING;

-- 2. SEED MASTER MINING CLAIMS
INSERT INTO mining_claims (
    claim_id, license_number, claim_name, claim_type, tenure_status,
    owner_id, operator_name, province, mining_district, ward_number, nearest_town,
    application_date, grant_date, expiry_date,
    area_hectares, perimeter_meters, beacons_count,
    projected_crs, geographic_crs,
    geom_wgs84, geom_arc1950, centroid_lat, centroid_lng,
    has_discovery_point, dp_geom_wgs84, dp_easting_arc1950, dp_northing_arc1950,
    dp_tie_beacon_id, dp_tie_bearing_str, dp_tie_bearing_deg, dp_tie_distance_meters,
    beacons_ledger_json, compliance_score, ema_eia_certificate_no, zimparks_status,
    production_stage, monthly_tonnage_extracted, active_workforce
) VALUES
-- Claim 1: Matanga Mine - Simba (Mberengwa Gold)
(
    'ZIM-MBE-001',
    'MC-HAR-202609081',
    'Matanga Mine - Simba',
    'Precious Metals (Gold/Silver)',
    'Active Gazetted',
    'OWN-ZW-005',
    'Matanga Artisanal Syndicate',
    'Midlands',
    'Mberengwa',
    'Ward 14 (Matanga)',
    'Mberengwa',
    '2024-03-12', '2024-06-01', '2034-05-31',
    420.0000, 8400.00, 4,
    'EPSG:20936', 'EPSG:4326',
    ST_GeomFromText('POLYGON((30.180 -20.750, 30.220 -20.750, 30.220 -20.780, 30.180 -20.780, 30.180 -20.750))', 4326),
    ST_Transform(ST_GeomFromText('POLYGON((30.180 -20.750, 30.220 -20.750, 30.220 -20.780, 30.180 -20.780, 30.180 -20.750))', 4326), 20936),
    -20.765000, 30.200000,
    TRUE,
    ST_GeomFromText('POINT(30.200 -20.765)', 4326),
    312450.00, 7702800.00,
    'B1', '044° 12'' 18"', 44.20, 245.80,
    '[
        {"peg": "B1", "easting": 310370, "northing": 7704460, "lat": -20.750, "lng": 30.180},
        {"peg": "B2", "easting": 314540, "northing": 7704460, "lat": -20.750, "lng": 30.220},
        {"peg": "B3", "easting": 314540, "northing": 7701140, "lat": -20.780, "lng": 30.220},
        {"peg": "B4", "easting": 310370, "northing": 7701140, "lat": -20.780, "lng": 30.180}
    ]'::jsonb,
    96, 'EMA-EIA-MID-2024-091', 'UNENCUMBERED_CLEARED',
    'Active Extraction', 650.00, 84
),
-- Claim 2: Selukwe Chrome Concession (Shurugwi Great Dyke)
(
    'ZIM-GD-001',
    'MC-SHU-2024-8841',
    'Selukwe Chrome Concession',
    'Chrome & Iron Ore (Podiform/Stratiform)',
    'Active Gazetted',
    'OWN-ZW-001',
    'ZIMASCO Surface Extraction Syndicate',
    'Midlands',
    'Shurugwi',
    'Ward 3 (Peak Mine)',
    'Shurugwi',
    '2022-01-10', '2022-05-15', '2032-05-14',
    340.5000, 7600.00, 4,
    'EPSG:20936', 'EPSG:4326',
    ST_GeomFromText('POLYGON((29.985 -19.650, 30.025 -19.650, 30.025 -19.690, 29.985 -19.690, 29.985 -19.650))', 4326),
    ST_Transform(ST_GeomFromText('POLYGON((29.985 -19.650, 30.025 -19.650, 30.025 -19.690, 29.985 -19.690, 29.985 -19.650))', 4326), 20936),
    -19.670000, 30.005000,
    TRUE,
    ST_GeomFromText('POINT(30.005 -19.670)', 4326),
    290800.00, 7824100.00,
    'B1', '038° 45'' 10"', 38.75, 310.20,
    '[
        {"peg": "B1", "easting": 288700, "northing": 7826320, "lat": -19.650, "lng": 29.985},
        {"peg": "B2", "easting": 292890, "northing": 7826320, "lat": -19.650, "lng": 30.025},
        {"peg": "B3", "easting": 292890, "northing": 7821890, "lat": -19.690, "lng": 30.025},
        {"peg": "B4", "easting": 288700, "northing": 7821890, "lat": -19.690, "lng": 29.985}
    ]'::jsonb,
    94, 'EMA-EIA-MID-2022-441', 'UNENCUMBERED_CLEARED',
    'Active Extraction', 450.00, 110
),
-- Claim 3: Hartley Complex PGM Block (Chegutu Great Dyke)
(
    'ZIM-GD-002',
    'MC-CHE-2023-1092',
    'Hartley Complex PGM Block',
    'Platinum Group Metals (PGM/MSZ)',
    'Active Gazetted',
    'OWN-ZW-002',
    'Zimplats Hartley Syndicate',
    'Mashonaland West',
    'Chegutu',
    'Ward 12 (Ngezi)',
    'Chegutu',
    '2021-08-15', '2023-02-01', '2043-01-31',
    850.0000, 12800.00, 4,
    'EPSG:20936', 'EPSG:4326',
    ST_GeomFromText('POLYGON((30.260 -18.130, 30.300 -18.130, 30.300 -18.170, 30.260 -18.170, 30.260 -18.130))', 4326),
    ST_Transform(ST_GeomFromText('POLYGON((30.260 -18.130, 30.300 -18.130, 30.300 -18.170, 30.260 -18.170, 30.260 -18.130))', 4326), 20936),
    -18.150000, 30.280000,
    TRUE,
    ST_GeomFromText('POINT(30.280 -18.150)', 4326),
    318200.00, 7992400.00,
    'B1', '045° 00'' 00"', 45.00, 420.50,
    '[
        {"peg": "B1", "easting": 316080, "northing": 7994620, "lat": -18.130, "lng": 30.260},
        {"peg": "B2", "easting": 320320, "northing": 7994620, "lat": -18.130, "lng": 30.300},
        {"peg": "B3", "easting": 320320, "northing": 7990190, "lat": -18.170, "lng": 30.300},
        {"peg": "B4", "easting": 316080, "northing": 7990190, "lat": -18.170, "lng": 30.260}
    ]'::jsonb,
    98, 'EMA-EIA-MSW-2023-012', 'UNENCUMBERED_CLEARED',
    'Active Extraction', 1200.00, 240
),
-- Claim 4: Kadoma Central Gold Corridor (Kadoma Greenstone Belt)
(
    'ZIM-GB-003',
    'MC-KAD-2025-0451',
    'Kadoma Central Gold Corridor',
    'Precious Metals (Gold/Silver)',
    'Active Gazetted',
    'OWN-ZW-003',
    'Kadoma Artisanal Syndicate',
    'Mashonaland West',
    'Kadoma',
    'Ward 8 (Patchway)',
    'Kadoma',
    '2023-06-20', '2025-01-15', '2035-01-14',
    210.0000, 5800.00, 4,
    'EPSG:20936', 'EPSG:4326',
    ST_GeomFromText('POLYGON((29.890 -18.310, 29.920 -18.310, 29.920 -18.340, 29.890 -18.340, 29.890 -18.310))', 4326),
    ST_Transform(ST_GeomFromText('POLYGON((29.890 -18.310, 29.920 -18.310, 29.920 -18.340, 29.890 -18.340, 29.890 -18.310))', 4326), 20936),
    -18.325000, 29.905000,
    TRUE,
    ST_GeomFromText('POINT(29.905 -18.325)', 4326),
    278600.00, 7972800.00,
    'B1', '035° 20'' 15"', 35.34, 180.40,
    '[
        {"peg": "B1", "easting": 277010, "northing": 7974460, "lat": -18.310, "lng": 29.890},
        {"peg": "B2", "easting": 280190, "northing": 7974460, "lat": -18.310, "lng": 29.920},
        {"peg": "B3", "easting": 280190, "northing": 7971140, "lat": -18.340, "lng": 29.920},
        {"peg": "B4", "easting": 277010, "northing": 7971140, "lat": -18.340, "lng": 29.890}
    ]'::jsonb,
    82, 'EMA-EIA-MSW-2024-889', 'UNENCUMBERED_CLEARED',
    'Active Extraction', 380.00, 95
),
-- Claim 5: Bikita Pegmatite Lithium Zone (Bikita Masvingo)
(
    'ZIM-PEG-004',
    'MC-BIK-2024-3329',
    'Bikita Pegmatite Lithium Zone',
    'Strategic Minerals (Lithium/Rare Earths)',
    'Active Gazetted',
    'OWN-ZW-004',
    'Bikita Minerals Extraction Syndicate',
    'Masvingo',
    'Bikita',
    'Ward 5 (Bikita Mine)',
    'Nyika / Masvingo',
    '2022-09-10', '2024-03-01', '2044-02-28',
    620.0000, 10200.00, 4,
    'EPSG:20936', 'EPSG:4326',
    ST_GeomFromText('POLYGON((31.420 -19.950, 31.460 -19.950, 31.460 -19.990, 31.420 -19.990, 31.420 -19.950))', 4326),
    ST_Transform(ST_GeomFromText('POLYGON((31.420 -19.950, 31.460 -19.950, 31.460 -19.990, 31.420 -19.990, 31.420 -19.950))', 4326), 20936),
    -19.970000, 31.440000,
    TRUE,
    ST_GeomFromText('POINT(31.440 -19.970)', 4326),
    441300.00, 7791800.00,
    'B1', '042° 10'' 05"', 42.17, 340.00,
    '[
        {"peg": "B1", "easting": 439210, "northing": 7794010, "lat": -19.950, "lng": 31.420},
        {"peg": "B2", "easting": 443390, "northing": 7794010, "lat": -19.950, "lng": 31.460},
        {"peg": "B3", "easting": 443390, "northing": 7789580, "lat": -19.990, "lng": 31.460},
        {"peg": "B4", "easting": 439210, "northing": 7789580, "lat": -19.990, "lng": 31.420}
    ]'::jsonb,
    96, 'EMA-EIA-MAS-2023-109', 'UNENCUMBERED_CLEARED',
    'Active Extraction', 1800.00, 320
),
-- Claim 6: Gwanda Greenstone Belt Claims (Gwanda Matabeleland South)
(
    'ZIM-GB-005',
    'MC-GWA-2023-7714',
    'Gwanda Greenstone Belt Claims',
    'Precious Metals (Gold/Silver)',
    'Active Gazetted',
    'OWN-ZW-006',
    'Gwanda Artisanal Syndicate',
    'Matabeleland South',
    'Gwanda',
    'Ward 4 (Colleen Bawn)',
    'Gwanda',
    '2021-04-18', '2023-01-10', '2033-01-09',
    180.0000, 5400.00, 4,
    'EPSG:20935', 'EPSG:4326',
    ST_GeomFromText('POLYGON((29.000 -20.920, 29.030 -20.920, 29.030 -20.950, 29.000 -20.950, 29.000 -20.920))', 4326),
    ST_Transform(ST_GeomFromText('POLYGON((29.000 -20.920, 29.030 -20.920, 29.030 -20.950, 29.000 -20.950, 29.000 -20.920))', 4326), 20935),
    -20.935000, 29.015000,
    TRUE,
    ST_GeomFromText('POINT(29.015 -20.935)', 4326),
    709400.00, 7683900.00,
    'B1', '036° 15'' 00"', 36.25, 195.60,
    '[
        {"peg": "B1", "easting": 707840, "northing": 7685560, "lat": -20.920, "lng": 29.000},
        {"peg": "B2", "easting": 710960, "northing": 7685560, "lat": -20.920, "lng": 29.030},
        {"peg": "B3", "easting": 710960, "northing": 7682240, "lat": -20.950, "lng": 29.030},
        {"peg": "B4", "easting": 707840, "northing": 7682240, "lat": -20.950, "lng": 29.000}
    ]'::jsonb,
    78, 'EMA-EIA-MTS-2023-552', 'UNENCUMBERED_CLEARED',
    'Development', 210.00, 65
)
ON CONFLICT (claim_id) DO NOTHING;

-- 3. SEED GEOLOGICAL STANDARD SPECIFICATIONS
INSERT INTO claim_geology (
    claim_id, primary_commodity, commodity_code, secondary_commodities,
    metallogenic_province, subchamber_or_belt, geological_formation, geological_age_era,
    host_rock, hanging_wall_lithology, foot_wall_lithology,
    deposit_genesis, mineralization_style, primary_ore_minerals, gangue_minerals,
    structural_controls, fault_trend, dip_angle_degrees, dip_direction,
    strike_length_meters, average_true_thickness_m, depth_to_orebody_m,
    alteration_style, weathering_profile_depth_m, gossan_indicator_present,
    spectral_band_math_signature, resource_compliance_code, estimated_resource_tonnage_mt,
    average_ore_grade, cut_off_grade, contained_metal_content, resource_category
) VALUES
-- Claim 1: Matanga Mine - Simba (Gold)
(
    'ZIM-MBE-001',
    'Gold (Au)', 'Au', ARRAY['Silver', 'Antimony'],
    'Mberengwa Archaean Greenstone Belt', 'Belingwe Belt East Corridor',
    'Bulawayan Group Greenstones', 'Archaean (~2.7 Ga)',
    'Quartz-Carbonate Vein in Chlorite-Talc Schist', 'Basaltic Komatiite', 'Banded Iron Formation (BIF)',
    'Orogenic Lode Gold (Shear-Hosted)', 'Hydrothermal Quartz Shear Lode',
    ARRAY['Native Gold (Au)', 'Electrum', 'Pyrite', 'Arsenopyrite'],
    ARRAY['Quartz', 'Ankerite', 'Calcite', 'Chlorite', 'Sericite'],
    'Brittle-Ductile Shear Zone abutting BIF contact', 'NNE-SSW 025°', 65.0, 'East',
    1450.00, 2.80, 0.00,
    'Silicification, Carbonatization & Sericitization with Pyritic Halo', 18.50, TRUE,
    'Sentinel-2 B4/B2 (Iron Oxide Gossan) & B11/B12 (Hydrothermal Clay)',
    'SAMREC / JORC 2012', 2.850,
    '4.85 g/t Au', '1.20 g/t Au', '444,000 oz Contained Gold', 'Measured & Indicated'
),
-- Claim 2: Selukwe Chrome Concession
(
    'ZIM-GD-001',
    'Chromite & PGM', 'Cr', ARRAY['Platinum', 'Palladium', 'Nickel'],
    'Great Dyke Layered Ultramafic Complex', 'Selukwe Subchamber Horizon',
    'Great Dyke Ultramafic Sequence', 'Archaean (2.575 Ga)',
    'Chromitite Seam hosted in Dunite / Harzburgite', 'Pyroxenite Layer P1', 'Dunite Floor Cumulate',
    'Stratiform Magmatic Layered PGM-Cr Reef (MSZ Type)', 'Massive Seam & Podiform Chromitite',
    ARRAY['Chromite (FeCr2O4)', 'Braggite', 'Sperrylite', 'Pentlandite'],
    ARRAY['Serpentine', 'Olivine', 'Orthopyroxene', 'Talc', 'Magnetite'],
    'Transverse Graben Synclinal Keel Faulting', 'N-S 005°', 14.5, 'Inward Synclinal (East)',
    2800.00, 1.40, 0.00,
    'Serpentinization and Talc-Carbonate Alteration', 12.00, FALSE,
    'Sentinel-2 Ferrous Iron SWIR2/NIR Peak (B12/B8)',
    'JORC 2012', 8.200,
    '44.5% Cr2O3 (Cr:Fe ratio 2.4:1)', '32.0% Cr2O3', '3.65 Million Tonnes Lump Chrome', 'Measured'
),
-- Claim 3: Hartley Complex PGM Block
(
    'ZIM-GD-002',
    'Platinum Group Metals (PGM)', 'PGE', ARRAY['Palladium', 'Rhodium', 'Gold', 'Nickel', 'Copper'],
    'Great Dyke Layered Ultramafic Complex', 'Hartley Subchamber (Ngezi Basin)',
    'Main Sulphide Zone (MSZ) Horizon', 'Archaean (2.575 Ga)',
    'Bronzitite / Pyroxenite P1 Cumulate Layer', 'Gabbro-Norite Sequence', 'Harzburgite Footwall',
    'Stratiform Magmatic Layered PGM-Cr Reef (MSZ Type)', 'Disseminated PGE-Cu-Ni Intercumulus Sulfides',
    ARRAY['Sperrylite (PtAs2)', 'Braggite ((Pt,Pd,Ni)S)', 'Kotulskite', 'Chalcopyrite', 'Pentlandite'],
    ARRAY['Enstatite', 'Augite', 'Plagioclase', 'Biotite', 'Pyrrhotite'],
    'Axial Synclinal Trough Structure with Mild Transverse Shears', 'NNE-SSW 018°', 8.5, 'Gentle Basin Dip (East)',
    4200.00, 2.10, 45.00,
    'Pristine Magmatic Cumulate (Minimal Hydrothermal Alteration)', 8.00, FALSE,
    'Sentinel-2 Pyroxene Absorption Band (B11 SWIR1)',
    'JORC 2012 / SAMREC', 24.500,
    '3.92 g/t 4E (Pt+Pd+Rh+Au)', '1.80 g/t 4E', '3.08 Million Ounces 4E PGE', 'Measured'
),
-- Claim 4: Kadoma Central Gold Corridor
(
    'ZIM-GB-003',
    'Gold (Au)', 'Au', ARRAY['Silver', 'Copper'],
    'Midlands Archaean Greenstone Belt', 'Kadoma-Gweru Gold Belt',
    'Bulawayan Felsic Pyroclastics & Basalts', 'Archaean (~2.65 Ga)',
    'Quartz Lode in Metabasaltic Greenstone', 'Quartz Porphyry', 'Carbonaceous Metasediments',
    'Orogenic Lode Gold (Shear-Hosted)', 'Crack-Seal Hydrothermal Quartz Lode',
    ARRAY['Visible Native Gold', 'Tellurides', 'Pyrite', 'Chalcopyrite'],
    ARRAY['Milky Quartz', 'Tourmaline', 'Ankerite', 'Chlorite'],
    'Munyati River Shear Zone Splays', 'NW-SE 315°', 72.0, 'Southwest',
    1100.00, 1.85, 0.00,
    'Intense Silicification, Tourmalinization and Carbonatization', 22.00, TRUE,
    'Sentinel-2 Iron Oxide Gossan (B4/B2) & reNDVI',
    'SAMREC', 1.450,
    '5.40 g/t Au', '1.50 g/t Au', '251,700 oz Contained Gold', 'Indicated'
),
-- Claim 5: Bikita Pegmatite Lithium Zone
(
    'ZIM-PEG-004',
    'Lithium (Li)', 'Li', ARRAY['Tantalum (Ta)', 'Beryllium (Be)', 'Cesium (Cs)'],
    'Bikita Pegmatite Belt', 'Al Hayat - Bikita Main Sector',
    'Archaean Victoria Greenstone Belt Border', 'Archaean (~2.62 Ga)',
    'Zoned LCT Granitic Pegmatite Intrusive', 'Metavolcanic Greenstone', 'Porphyritic Biotite Granite',
    'LCT Granitic Pegmatite (Spodumene/Petalite)', 'Zoned Giant Complex Pegmatite Body',
    ARRAY['Petalite (LiAlSi4O10)', 'Spodumene (LiAlSi2O6)', 'Bikitaite', 'Pollucite', 'Tantalite'],
    ARRAY['Albite', 'Microcline', 'Quartz', 'Muscovite', 'Lepidolite'],
    'Extensional Fracture System within Archaean Amphibolite Schists', 'NNE-SSW 030°', 28.0, 'East',
    2400.00, 14.50, 0.00,
    'Greisenization, Albitization and Fluorite Impregnation', 6.50, FALSE,
    'Sentinel-2 SWIR1/SWIR2 Hydrothermal Clay & Lithium Alteration',
    'JORC 2012', 65.400,
    '1.68% Li2O', '0.50% Li2O', '1.09 Million Tonnes LCE (Lithium Carbonate Equivalent)', 'Measured & Indicated'
),
-- Claim 6: Gwanda Greenstone Belt Claims
(
    'ZIM-GB-005',
    'Gold (Au)', 'Au', ARRAY['Silver', 'Antimony'],
    'Gwanda Archaean Greenstone Belt', 'Colleen Bawn - Jessie Corridor',
    'Lower Bulawayan Ultramafics & BIFs', 'Archaean (~2.7 Ga)',
    'Banded Iron Formation (BIF) Hosted Shear Veins', 'Amphibolite', 'Serpentinized Dunite',
    'Banded Iron Formation (BIF Hosted Au/Fe)', 'Sulfide Replacement in Magnetite BIF Layers',
    ARRAY['Native Gold (Au)', 'Arsenopyrite', 'Pyrrhotite', 'Stibnite'],
    ARRAY['Magnetite', 'Quartz', 'Siderite', 'Grünerite'],
    'Gwanda Anticlinal Flank Shear Splays', 'E-W 090°', 80.0, 'North',
    950.00, 2.20, 15.00,
    'Sulfidation of BIF (Magnetite to Pyrrhotite/Pyrite) with Quartz Stringers', 20.00, TRUE,
    'Sentinel-2 Iron Oxide Band Math (B4/B2)',
    'SAMREC', 0.920,
    '4.15 g/t Au', '1.30 g/t Au', '122,700 oz Contained Gold', 'Inferred'
)
ON CONFLICT (claim_id) DO NOTHING;

