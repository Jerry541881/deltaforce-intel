-- ========================================
-- 三角洲情报站 数据库 Schema
-- 在 Supabase SQL Editor 中执行
-- ========================================

-- 1. 枪械分类表
CREATE TABLE IF NOT EXISTS weapon_categories (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  display_order INT DEFAULT 0
);

-- 2. 强度分组表 (T0/T1/T2)
CREATE TABLE IF NOT EXISTS tier_levels (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  display_order INT DEFAULT 0
);

-- 3. 改枪码主表
CREATE TABLE IF NOT EXISTS weapon_builds (
  id BIGSERIAL PRIMARY KEY,
  weapon_name TEXT NOT NULL,
  category_id INT REFERENCES weapon_categories(id),
  tier_id INT REFERENCES tier_levels(id),
  build_code TEXT NOT NULL,
  title TEXT,
  description TEXT,
  source_url TEXT,
  source_platform TEXT,
  author TEXT,
  tags TEXT[],
  view_count INT DEFAULT 0,
  like_count INT DEFAULT 0,
  confidence_score DECIMAL(3,2) DEFAULT 0.5,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_builds_category ON weapon_builds(category_id);
CREATE INDEX IF NOT EXISTS idx_builds_tier ON weapon_builds(tier_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_builds_code_unique ON weapon_builds(build_code);

-- 4. 地图表
CREATE TABLE IF NOT EXISTS maps (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT
);

-- 5. 跑刀路线表
CREATE TABLE IF NOT EXISTS route_guides (
  id BIGSERIAL PRIMARY KEY,
  map_id INT REFERENCES maps(id),
  title TEXT NOT NULL,
  difficulty TEXT DEFAULT 'medium',
  expected_loot TEXT,
  risk_level TEXT DEFAULT 'medium',
  steps JSONB,
  video_url TEXT,
  map_image_url TEXT,
  waypoints JSONB,
  author TEXT,
  source_url TEXT,
  confidence_score DECIMAL(3,2) DEFAULT 0.5,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_routes_map ON route_guides(map_id);

-- 6. 每日密码表
CREATE TABLE IF NOT EXISTS daily_codes (
  id BIGSERIAL PRIMARY KEY,
  code_date DATE NOT NULL UNIQUE,
  code_value TEXT NOT NULL,
  source_count INT DEFAULT 1,
  sources JSONB,
  confidence DECIMAL(3,2) DEFAULT 0.5,
  verified BOOLEAN DEFAULT FALSE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. 干员分析表
CREATE TABLE IF NOT EXISTS operator_analysis (
  id BIGSERIAL PRIMARY KEY,
  operator_name TEXT NOT NULL,
  role TEXT,
  overall_rating DECIMAL(3,1),
  strengths TEXT[],
  weaknesses TEXT[],
  best_maps TEXT[],
  best_weapons TEXT[],
  playstyle TEXT,
  tips TEXT,
  analysis_text TEXT,
  version TEXT,
  source_urls TEXT[],
  confidence_score DECIMAL(3,2) DEFAULT 0.5,
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_operator_name ON operator_analysis(operator_name);

-- ============ 初始化数据 ============

-- 枪械分类
INSERT INTO weapon_categories (name, display_order) VALUES
  ('突击步枪', 1),
  ('冲锋枪', 2),
  ('狙击枪', 3),
  ('战斗步枪', 4),
  ('轻机枪', 5),
  ('霰弹枪', 6),
  ('手枪', 7)
ON CONFLICT (name) DO NOTHING;

-- 强度分组
INSERT INTO tier_levels (name, display_order) VALUES
  ('T0', 1),
  ('T1', 2),
  ('T2', 3)
ON CONFLICT (name) DO NOTHING;

-- 地图
INSERT INTO maps (name, description) VALUES
  ('零号大坝', '入门级地图，资源丰富'),
  ('航天基地', '中高级地图，高价值物资'),
  ('巴克什', '巷战地图，适合老六'),
  ('终极战场', '高难度地图，顶级装备')
ON CONFLICT (name) DO NOTHING;

-- ============ 行级安全策略 ============

ALTER TABLE weapon_builds ENABLE ROW LEVEL SECURITY;
ALTER TABLE route_guides ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE operator_analysis ENABLE ROW LEVEL SECURITY;

-- 公开读取
DROP POLICY IF EXISTS "public_read_builds" ON weapon_builds;
CREATE POLICY "public_read_builds" ON weapon_builds FOR SELECT USING (true);

DROP POLICY IF EXISTS "public_read_routes" ON route_guides;
CREATE POLICY "public_read_routes" ON route_guides FOR SELECT USING (true);

DROP POLICY IF EXISTS "public_read_codes" ON daily_codes;
CREATE POLICY "public_read_codes" ON daily_codes FOR SELECT USING (true);

DROP POLICY IF EXISTS "public_read_operators" ON operator_analysis;
CREATE POLICY "public_read_operators" ON operator_analysis FOR SELECT USING (true);

-- 写入策略（仅 service_role）
DROP POLICY IF EXISTS "service_write_builds" ON weapon_builds;
CREATE POLICY "service_write_builds" ON weapon_builds FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_write_routes" ON route_guides;
CREATE POLICY "service_write_routes" ON route_guides FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_write_codes" ON daily_codes;
CREATE POLICY "service_write_codes" ON daily_codes FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_write_operators" ON operator_analysis;
CREATE POLICY "service_write_operators" ON operator_analysis FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============ 完成 ============
-- 验证
SELECT 'weapon_categories' as table_name, COUNT(*) FROM weapon_categories
UNION ALL SELECT 'tier_levels', COUNT(*) FROM tier_levels
UNION ALL SELECT 'maps', COUNT(*) FROM maps;
