CREATE TABLE IF NOT EXISTS grouping_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 分组ID
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 分组时间
    group_name TEXT NOT NULL,  -- 分组名称
    is_public BOOLEAN NOT NULL DEFAULT TRUE,  -- 是否公开
    private_password TEXT,  -- 私有分组密码
    source_elements TEXT NOT NULL,  -- 待分组元素
    result TEXT NOT NULL,  -- 分组结果
    
    -- 创建索引以便快速搜索
    CREATE INDEX idx_group_name ON grouping_results(group_name);
    CREATE INDEX idx_created_at ON grouping_results(created_at DESC);
);