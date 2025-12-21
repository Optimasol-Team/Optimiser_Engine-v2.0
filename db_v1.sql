CREATE DATABASE  IF NOT EXISTS `db_engine` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `db_engine`;
-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: db_engine
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `clients`
--

DROP TABLE IF EXISTS `clients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clients` (
  `client_id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `tilt` decimal(8,2) DEFAULT NULL,
  `azimuth` decimal(8,2) DEFAULT NULL,
  `router_id` varchar(50) DEFAULT NULL,
  `pwd` varchar(50) DEFAULT NULL,
  `gradation` boolean DEFAULT FALSE,
  `mode` enum(`AutoCons`, `cost`) DEFAULT `AutoCons`,
  PRIMARY KEY (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

INSERT INTO `clients` 
(`client_id`, `nom`, `email`, `latitude`, `longitude`, `tilt`, `azimuth`, `router_id`, `pwd`) 
VALUES 
(1, 'Admin', '', 0, 0, 0.00, 0.00, '', 
'$2b$12$YUs0XL4wLsQk79JLhaJmLuvQZrIkzXdc7vjyZNDINpGFR4gxCUBMy');

--
-- Table structure for table `consignes`
--

DROP TABLE IF EXISTS `consignes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consignes` (
  `consigne_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int DEFAULT NULL,
  `day` int NOT NULL,
  `moment` time NOT NULL,
  `capacite_litres` decimal(8,2) DEFAULT NULL,
  `puissance_kw` decimal(8,2) DEFAULT 30.0,
  PRIMARY KEY (`consigne_id`),
  KEY `client_id` (`client_id`),
  UNIQUE KEY `unique_client_day_moment` (`client_id`, `day`, `moment`),
  CONSTRAINT `consignes_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `plages_interdites`
--

DROP TABLE IF EXISTS `plages_interdites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `plages_interdites` (
  `plage_interdite_id` int NOT NULL AUTO_INCREMENT,
  `constraint_id` int DEFAULT NULL,
  `heure_debut` time NOT NULL,
  `heure_fin` time NOT NULL,
  PRIMARY KEY (`plage_interdite_id`),
  KEY `constraint_id` (`constraint_id`),
  CHECK (`heure_debut` < `heure_fin`),
  UNIQUE KEY `unique_constraint_debut_fin` (`constraint_id`, `heure_debut`, `heure_fin`),
  CONSTRAINT `plages_interdites_ibfk_1` FOREIGN KEY (`constraint_id`) REFERENCES `constraints` (`constraint_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `constraints`
--

DROP TABLE IF EXISTS `constraints`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `constraints` (
  `constraint_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int DEFAULT NULL,
  `temperature_minimale` decimal(2,2) DEFAULT 10.0,
  `puissance_maison` decimal(8,2) DEFAULT 0.0,
  PRIMARY KEY (`constraint_id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `constraints_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=123 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `features`
--

DROP TABLE IF EXISTS `features`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `features` (
  `feature_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int DEFAULT NULL,
  `gradation` boolean DEFAULT FALSE,
  `mode` enum(`AutoCons`, `cost`) DEFAULT `AutoCons`,
  PRIMARY KEY (`feature_id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `features_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `creneaux_hp`
--

DROP TABLE IF EXISTS `creneaux_hp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `creneaux_hp` (
  `creneau_hp_id` int NOT NULL AUTO_INCREMENT,
  `heure_debut` time NOT NULL,
  `heure_fin` time NOT NULL,
  PRIMARY KEY (`creneau_hp_id`),
  UNIQUE KEY `unique_debut_fin` (`heure_debut`, `heure_fin`),
  CHECK (`heure_debut` < `heure_fin`)
) ENGINE=InnoDB AUTO_INCREMENT=78 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `prices`
--

DROP TABLE IF EXISTS `prices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prices` (
  `type` enum(`base`, `hp`, `hc`, `revente`) NOT NULL,
  `prix` decimal(5,2) NOT NULL,
  PRIMARY KEY (`type`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `water_heaters`
--

DROP TABLE IF EXISTS `water_heaters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `water_heaters` (
  `water_heater_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int DEFAULT NULL,
  `volume_litres` decimal(8,2) NOT NULL,
  `power_watts` decimal(5,2) NOT NULL,
  `coeff_isolation` decimal(5,2) DEFAULT 0.0,
  `temperature_eau_froide_celsius` decimal(2,2) DEFAULT 10.0,
  PRIMARY KEY (`water_heater_id`),
  CONSTRAINT `water_heaters_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=873 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;