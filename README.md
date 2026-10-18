# 🌊 StudyTide // Campus Soundscape Telemetry

> Real-time acoustic telemetry and sensory-safe study space matching powered by Tiger Data continuous time-series aggregation.

## Overview
Subjective noise ratings fail students—particularly neurodivergent learners who require sensory predictability. StudyTide transforms campus devices and IoT edge sensors into acoustic telemetry nodes, streaming continuous decibel ($dB$) pings directly into Tiger Data.

## Architecture & Tiger Data Integration
- **High-Throughput Telemetry Ingestion:** Continuous sensory feeds stream into Tiger Data PostgreSQL storage via time-stamped transactional pings.
- **Dynamic Thresholding:** Differentiates acceptable ambient acoustic baselines across spaces (e.g., solo silent carrels vs. group collaboration commons).
- **Time-Bucket Aggregation:** Employs PostgreSQL's `date_trunc` aggregation directly inside Tiger Data to compute 90-minute rolling acoustic trends without client-side compute overhead.

## Tech Stack
- **Database Engine:** Tiger Data (Managed Timescale / PostgreSQL)
- **Frontend & App Engine:** Python, Streamlit, Pandas
- **Styling:** Monospace Hacker UI & Devpost Aesthetic