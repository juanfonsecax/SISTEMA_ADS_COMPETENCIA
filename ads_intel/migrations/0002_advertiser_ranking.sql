ALTER TABLE advertiser ADD COLUMN reported_real_active_ads INTEGER;
ALTER TABLE advertiser ADD COLUMN reported_captured_creatives INTEGER;
ALTER TABLE advertiser ADD COLUMN reported_meta_cc_instances INTEGER;
ALTER TABLE advertiser ADD COLUMN reported_duplication_intensity REAL;
ALTER TABLE advertiser ADD COLUMN reported_catalog_pct REAL;
ALTER TABLE advertiser ADD COLUMN ranking_verdict TEXT;
