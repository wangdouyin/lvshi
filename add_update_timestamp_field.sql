-- 为case表添加update_timestamp字段
-- 执行此SQL脚本来更新现有数据库

ALTER TABLE `case` 
ADD COLUMN `update_timestamp` INT NULL COMMENT '消息更新时间' 
AFTER `lawyer_last_timestamp`;
