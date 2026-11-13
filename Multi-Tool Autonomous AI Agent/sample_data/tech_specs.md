# Datheon High-Performance AI Cluster Specifications

## Overview
This document specifies the cluster hardware, network topologies, and power ratings
for Datheon's primary inference and training infrastructure as of 2026.

## Cluster Node Configurations

### 1. Training Nodes (Type: Alpha-H100)
- **Node Quantity**: 32 servers
- **Accelerators per Node**: 8x NVIDIA H100 SXM5 80GB HBM3
- **Total Cluster GPUs**: 256 GPUs
- **System Memory**: 2,048 GB DDR5 ECC per node
- **Local NVMe Storage**: 30.72 TB U.2 PCIe Gen 5 per node
- **Interconnect**: 8x 400Gb/s InfiniBand NDR links per node
- **Thermal Design Power (TDP)**: 10.2 kW per rack chassis

### 2. Inference & Real-time Serving Nodes (Type: Beta-L40S)
- **Node Quantity**: 64 servers
- **Accelerators per Node**: 4x NVIDIA L40S 48GB GDDR6
- **Total Inference GPUs**: 256 GPUs
- **System Memory**: 512 GB DDR5 per node
- **Network Interface**: Dual 100GbE QSFP28
- **Average Node Power Draw**: 1.85 kW

### 3. High-Speed Storage Fabric
- **Lustre Parallel Filesystem**: 1.5 Petabytes usable NVMe pool
- **Sequential Read Bandwidth**: 450 GB/s
- **Sequential Write Bandwidth**: 280 GB/s

## Operational Calculations Reference
- Total Peak FP8 Compute Capacity: 498.4 PFLOPS
- Daily Total Energy Consumption at 80% Utilization: 28,450 kWh
- Cooling PUE (Power Usage Effectiveness): 1.18
