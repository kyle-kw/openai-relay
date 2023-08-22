CREATE DATABASE IF NOT EXISTS openai;

use openai;

CREATE TABLE IF NOT EXISTS `auth_forward_api_keys_v2` (
  `record_pk` bigint NOT NULL AUTO_INCREMENT,
  `forward_key` varchar(1000) DEFAULT NULL COMMENT '鉴权key',
  `key_used` varchar(1000) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT 'any' COMMENT 'key 用户',
  `model` varchar(1000) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT 'any' COMMENT 'key 用户',
  `req_token_cnt` int DEFAULT '0' COMMENT '请求使用的token数',
  `res_token_cnt` int DEFAULT '0' COMMENT '响应使用的token数',
  `status` tinyint NOT NULL DEFAULT '0',
  `create_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '生成时间',
  `update_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (`record_pk`),
  UNIQUE KEY `idx_key` (`forward_key`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `auth_openai_api_keys_v2` (
  `record_pk` bigint NOT NULL AUTO_INCREMENT,
  `api_key` varchar(1000) NOT NULL COMMENT 'key',
  `key_type` varchar(1000) NOT NULL COMMENT 'key 用处类型',
  `key_used` varchar(1000) DEFAULT 'any' COMMENT 'key 允许使用的角色， any',
  `api_base` varchar(1000) DEFAULT '' COMMENT 'api base 地址',
  `api_type` varchar(1000) DEFAULT '' COMMENT 'api key 类型',
  `api_version` varchar(100) DEFAULT '' COMMENT 'api 版本',
  `model` varchar(1000) DEFAULT '' COMMENT '模型类型',
  `engine` varchar(1000) DEFAULT '' COMMENT '引擎类型',
  `limit_token` int DEFAULT '200' COMMENT '每分钟最大使用token数。单位：k',
  `req_token_cnt` int DEFAULT '0' COMMENT '请求使用token数',
  `res_token_cnt` int DEFAULT '0' COMMENT '响应使用token数',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT 'key状态',
  `subscribe` varchar(100) DEFAULT '' COMMENT '订阅类型',
  `available_area` varchar(100) DEFAULT '' COMMENT '可用区',
  `create_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '生成时间',
  `update_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (`record_pk`),
  UNIQUE KEY `idx_key` (`api_key`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `auth_forward_key_model_mapping` (
  `record_pk` bigint NOT NULL AUTO_INCREMENT,
  `forward_key` varchar(100) NOT NULL COMMENT '鉴权key',
  `old_model` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci COMMENT '源model',
  `new_model` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci COMMENT '新model',
  `status` tinyint NOT NULL DEFAULT '0',
  `create_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '生成时间',
  `update_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
  PRIMARY KEY (`record_pk`),
  UNIQUE KEY `idx_key` (`forward_key`, `old_model`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `openai_relay_log_info` (
  `record_pk` bigint NOT NULL AUTO_INCREMENT,
  `forward_key` varchar(100) NOT NULL COMMENT '验证使用key',
  `req_type` varchar(100) DEFAULT '' COMMENT '请求类型',
  `model_name` varchar(100) DEFAULT '' COMMENT '请求model名字',
  `req_prompt` text COMMENT '请求prompt',
  `res_content` text COMMENT '返回内容',
  `first_time` float DEFAULT '0' COMMENT '请求第一次返回内容用时',
  `all_time` float DEFAULT '0' COMMENT '请求整体用时',
  `return_rate` float DEFAULT '0' COMMENT '吐字/s',
  `retry_times` tinyint DEFAULT '0' COMMENT '重试次数',
  `req_token` int DEFAULT '0' COMMENT '请求使用token数',
  `res_token` int DEFAULT '0' COMMENT '响应使用token数',
  `log_info` text NOT NULL COMMENT '日志信息',
  `create_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '生成时间',
  PRIMARY KEY (`record_pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `openai_relay_log_info_error` (
  `record_pk` bigint NOT NULL AUTO_INCREMENT,
  `forward_key` varchar(100) NOT NULL COMMENT '验证使用key',
  `openai_key` varchar(100) NOT NULL COMMENT '请求使用key',
  `req_type` varchar(100) DEFAULT '' COMMENT '请求类型',
  `model_name` varchar(100) DEFAULT '' COMMENT '请求model名字',
  `req_prompt` text COMMENT '请求prompt',
  `log_info` text NOT NULL COMMENT '日志信息',
  `error_info` text NOT NULL COMMENT '错误信息',
  `create_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '生成时间',
  PRIMARY KEY (`record_pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

