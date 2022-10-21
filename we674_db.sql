/*
 Navicat Premium Data Transfer

 Source Server         : localhost
 Source Server Type    : MariaDB
 Source Server Version : 100421
 Source Host           : localhost:3306
 Source Schema         : we674_db

 Target Server Type    : MariaDB
 Target Server Version : 100421
 File Encoding         : 65001

 Date: 21/10/2022 21:52:23
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for img_dataset
-- ----------------------------
DROP TABLE IF EXISTS `img_dataset`;
CREATE TABLE `img_dataset` (
  `img_id` int(11) NOT NULL,
  `img_person` int(11) DEFAULT NULL,
  PRIMARY KEY (`img_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for person_data
-- ----------------------------
DROP TABLE IF EXISTS `person_data`;
CREATE TABLE `person_data` (
  `p_id` int(11) NOT NULL,
  `p_name` varchar(255) DEFAULT NULL,
  `p_created` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `p_status` tinyint(4) DEFAULT 1,
  PRIMARY KEY (`p_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
