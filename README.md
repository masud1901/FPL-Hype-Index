# FPL Data Collection System

A distributed data collection system for the FPL Transfer Predictor that collects data from multiple sources and stores it in a unified format.

## Project Structure

This project follows a modular architecture with separate components for:
- **Scrapers**: Independent modules for each data source
- **Processors**: ETL pipeline for data cleaning and validation
- **Storage**: Database models and data access layer
- **Orchestration**: Task scheduling and coordination
- **Utils**: Common utilities and helpers

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your environment variables
3. Run `docker-compose up` to start the system

## Development

- Use the develop branch for all development work
- Follow the commit-by-commit plan in `docs/commit by commit plan phase 1.md`
- Run tests with `pytest`

## Architecture

See `docs/data_collection_architecture.md` for detailed architecture documentation. 