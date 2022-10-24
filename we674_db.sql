/*
 Navicat Premium Data Transfer

 Source Server         : localhost
 Source Server Type    : MariaDB
 Source Server Version : 100424 (10.4.24-MariaDB)
 Source Host           : localhost:3306
 Source Schema         : we674_db

 Target Server Type    : MariaDB
 Target Server Version : 100424 (10.4.24-MariaDB)
 File Encoding         : 65001

 Date: 25/10/2022 00:04:35
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for check_in
-- ----------------------------
DROP TABLE IF EXISTS `check_in`;
CREATE TABLE `check_in`  (
  `c_id` int(11) NOT NULL AUTO_INCREMENT,
  `c_datetime` datetime NULL DEFAULT current_timestamp(),
  `p_id` int(11) NULL DEFAULT NULL,
  PRIMARY KEY (`c_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for img_dataset
-- ----------------------------
DROP TABLE IF EXISTS `img_dataset`;
CREATE TABLE `img_dataset`  (
  `img_id` int(11) NOT NULL,
  `img_person` int(11) NULL DEFAULT NULL,
  PRIMARY KEY (`img_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for person_data
-- ----------------------------
DROP TABLE IF EXISTS `person_data`;
CREATE TABLE `person_data`  (
  `p_id` int(11) NOT NULL,
  `p_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `p_created` datetime NULL DEFAULT current_timestamp() ON UPDATE CURRENT_TIMESTAMP,
  `p_status` tinyint(4) NULL DEFAULT 1,
  PRIMARY KEY (`p_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
