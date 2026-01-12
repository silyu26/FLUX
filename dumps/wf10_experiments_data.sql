-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: wf10
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
-- Table structure for table `experiments_data`
--

DROP TABLE IF EXISTS `experiments_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `experiments_data` (
  `id` int NOT NULL AUTO_INCREMENT,
  `req_id` int NOT NULL,
  `exp_id` int NOT NULL,
  `gen_at` datetime(3) NOT NULL,
  `server_in` datetime(3) DEFAULT NULL,
  `server_out` datetime(3) DEFAULT NULL,
  `model_in` datetime(3) NOT NULL,
  `model_out` datetime(3) NOT NULL,
  `minio_in` datetime(3) DEFAULT NULL,
  `minio_out` datetime(3) DEFAULT NULL,
  `db_in` datetime(3) DEFAULT NULL,
  `db_out` datetime(3) DEFAULT NULL,
  `dpse_in` datetime(3) DEFAULT NULL,
  `dpse_out` datetime(3) DEFAULT NULL,
  `cpu_usage` float DEFAULT NULL,
  `gpu_usage` float DEFAULT NULL,
  `gpu_vram_usage` float DEFAULT NULL,
  `gpu_temperature` float DEFAULT NULL,
  `gpu_power` float DEFAULT NULL,
  `memory_usage` float DEFAULT NULL,
  `process_count` int DEFAULT NULL,
  `fps` int DEFAULT NULL,
  `device` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `experiments_data`
--

LOCK TABLES `experiments_data` WRITE;
/*!40000 ALTER TABLE `experiments_data` DISABLE KEYS */;
/*!40000 ALTER TABLE `experiments_data` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-12 10:56:55
