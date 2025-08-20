# FPL Data Collection & Prediction System

A comprehensive, production-ready system for FPL data collection and transfer prediction that automatically collects, processes, and analyzes data from multiple sources to provide intelligent transfer recommendations.

## 🚀 Features

### Data Collection
- **Multi-Source Data Collection**: Automated scraping from 6+ data sources
- **Robust Error Handling**: Rate limiting, retry logic, and graceful failure recovery
- **Data Quality Assurance**: Comprehensive validation and cross-source verification
- **Production Monitoring**: Health checks, performance metrics, and operational visibility

### Prediction Engine
- **Advanced Player Scoring**: Multi-dimensional Player Impact Score (PIS) calculation
- **Transfer Optimization**: Intelligent transfer recommendations with risk assessment
- **Backtesting Framework**: Historical performance validation and strategy comparison
- **Confidence Scoring**: Reliability metrics for all predictions
- **Position-Specific Analysis**: Tailored scoring for GK, DEF, MID, FWD positions

### System Architecture
- **Scalable Architecture**: Modular design with Docker containerization
- **Comprehensive Testing**: Unit tests, integration tests, and automated validation
- **Redis Caching**: Performance optimization for expensive computations
- **RESTful API**: Complete API for data access and prediction services

## 📊 Data Sources

| Source            | Frequency | Data Type                | Status   |
| ----------------- | --------- | ------------------------ | -------- |
| **FPL API**       | Daily     | Player stats, team data  | ✅ Active |
| **Understat**     | Bi-weekly | xG, xA, advanced metrics | ✅ Active |
| **FBRef**         | Bi-weekly | Comprehensive statistics | ✅ Active |
| **Transfermarkt** | Bi-weekly | Market values, transfers | ✅ Active |
| **WhoScored**     | Bi-weekly | Performance ratings      | ✅ Active |
| **Football-Data** | Bi-weekly | Historical matches       | ✅ Active |

## 🏗️ Architecture

```
FPL Data Collection & Prediction System
├── Data Collection Layer
│   ├── Scrapers (6 data sources)
│   ├── Processors (ETL pipeline)
│   └── Storage (PostgreSQL)
├── Prediction Engine
│   ├── Feature Engineering
│   ├── Scoring Algorithms
│   ├── Transfer Optimization
│   └── Backtesting Framework
├── API Layer
│   ├── Data Access Endpoints
│   ├── Prediction Endpoints
│   └── Health Monitoring
├── Infrastructure
│   ├── Orchestration (Scheduler)
│   ├── Redis Caching
│   └── Docker Containerization
└── Utils (Rate limiting, retry logic, monitoring)
```

## 🛠️ Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for development)
- PostgreSQL (handled by Docker)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fpl-data-collection
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your configuration:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fpl_data
DB_USER=fpl_user
DB_PASSWORD=your_secure_password

# Scraper Configuration
SCRAPER_RATE_LIMIT_DELAY=1.0
SCRAPER_MAX_RETRIES=3
SCRAPER_REQUEST_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API Keys (if needed)
FOOTBALL_DATA_API_KEY=your_api_key
```

### 3. Start the System

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check system health
docker-compose exec scheduler python -c "
from orchestration.health_checker import get_health_summary
import asyncio
print(asyncio.run(get_health_summary()))
"
```

### 4. Verify Installation

```bash
# Check if all services are running
docker-compose ps

# Test data collection manually
docker-compose exec scheduler python scripts/run_scrapers.py --scraper fpl

# Run health check
docker-compose exec scheduler python -c "
from orchestration.health_checker import get_system_health
import asyncio
health = asyncio.run(get_system_health())
print(f'System Status: {health.overall_status}')
print(f'Healthy Scrapers: {health.healthy_scrapers}/{health.total_scrapers}')
"

# Test the API
curl http://localhost:8000/health
```

## 🧠 Prediction Engine

The FPL Prediction Engine provides intelligent transfer recommendations using advanced algorithms and comprehensive data analysis.

### Key Components

#### Player Impact Score (PIS)
- **Multi-dimensional scoring** combining form, fixtures, team performance, and value
- **Position-specific algorithms** for GK, DEF, MID, FWD positions
- **Confidence scoring** to assess prediction reliability
- **Risk assessment** including injury history and rotation risk

#### Transfer Optimization
- **Intelligent transfer recommendations** based on current squad analysis
- **Multiple strategies**: Balanced, Aggressive, Conservative
- **Constraint validation** ensuring FPL rule compliance
- **Expected points gain** calculation for each recommendation

#### Backtesting Framework
- **Historical performance validation** using past gameweek data
- **Strategy comparison** to identify optimal approaches
- **Performance metrics** including correlation, precision, and calibration scores
- **Risk-adjusted returns** analysis

### Usage Examples

#### Get Transfer Recommendations
```bash
# Using the API
curl -X POST "http://localhost:8000/api/v1/prediction/transfers/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "current_squad": {...},
    "available_players": [...],
    "strategy": "balanced",
    "max_transfers": 2
  }'
```

#### Calculate Player Scores
```bash
# Using the API
curl -X POST "http://localhost:8000/api/v1/prediction/scores/player" \
  -H "Content-Type: application/json" \
  -d '{
    "player": {
      "id": "player_123",
      "name": "Mohamed Salah",
      "position": "MID",
      "team": "Liverpool",
      "price": 13.0,
      "form": 8.2,
      "total_points": 220
    }
  }'
```

#### Run Backtest
```bash
# Using the command-line script
python scripts/run_prediction_backtest.py \
  --start-gw 1 \
  --end-gw 10 \
  --compare-strategies \
  --save-results results.json
```

#### Manual Optimization
```bash
# Using the command-line script
python scripts/run_prediction_optimization.py \
  --strategy balanced \
  --transfers 2 \
  --budget 2.0
```

## 🔧 Development

### Project Structure

```
fpl-data-collection/
├── config/                 # Configuration management
├── scrapers/              # Data source scrapers
│   ├── base/              # Abstract base classes
│   ├── fpl_api/           # FPL API scraper
│   ├── understat/         # Understat scraper
│   ├── fbref/             # FBRef scraper
│   ├── transfermarkt/     # Transfermarkt scraper
│   ├── whoscored/         # WhoScored scraper
│   └── football_data/     # Football-Data scraper
├── processors/            # ETL pipeline
├── storage/               # Database models and access
├── orchestration/         # Scheduling and coordination
├── prediction/            # Prediction engine
│   ├── features/          # Feature engineering
│   ├── scoring/           # Scoring algorithms
│   ├── optimization/      # Transfer optimization
│   └── validation/        # Backtesting framework
├── api/                   # REST API endpoints
│   └── routes/            # API route handlers
├── utils/                 # Common utilities
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

### Development Workflow

1. **Branch Strategy**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Testing**:
   ```bash
   # Run all tests
   pytest

   # Run specific test categories
   pytest tests/test_processors/
   pytest tests/test_scrapers/

   # Run with coverage
   pytest --cov=processors --cov=scrapers

   # Run integration tests
   docker-compose -f docker-compose.test.yml up --abort-on-container-exit
   ```

3. **Code Quality**:
   ```bash
   # Lint code
   flake8 processors/ scrapers/ utils/

   # Type checking
   mypy processors/ scrapers/ utils/
   ```

### Adding New Data Sources

1. Create scraper in `scrapers/new_source/`
2. Inherit from `BaseScraper`
3. Implement required methods
4. Add to coordinator registration
5. Update scheduler configuration
6. Add tests

Example:
```python
# scrapers/new_source/new_scraper.py
from scrapers.base.base_scraper import BaseScraper

class NewScraper(BaseScraper):
    async def scrape(self):
        # Implementation
        pass
    
    def validate_data(self, data):
        # Validation logic
        pass
```

## 📈 Monitoring & Operations

### Health Monitoring

The system includes comprehensive health monitoring:

```bash
# Get current health status
curl http://localhost:8000/health

# Export health report
docker-compose exec scheduler python -c "
from orchestration.health_checker import health_checker
import asyncio
asyncio.run(health_checker.export_health_report('/app/logs/health_report.json'))
"
```

### Logging

Structured logging with JSON format:

```bash
# View scraper logs
docker-compose logs scraper

# View scheduler logs
docker-compose logs scheduler

# View database logs
docker-compose logs database
```

### Performance Metrics

- **Success Rates**: Per-scraper success/failure tracking
- **Response Times**: API response time monitoring
- **Data Quality**: Validation error tracking
- **System Uptime**: Overall system availability

## 🧪 Testing

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline testing
- **Performance Tests**: Load and stress testing
- **Health Tests**: System health validation

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_processors/test_data_processor.py

# With verbose output
pytest -v

# Generate coverage report
pytest --cov=processors --cov=scrapers --cov-report=html
```

## 🔒 Production Deployment

### Security Considerations

- Use strong database passwords
- Implement API key rotation
- Monitor rate limits
- Regular security updates
- Backup strategies

### Scaling

- Horizontal scaling with multiple scraper instances
- Database connection pooling
- Redis caching for rate limiting
- Load balancing for high availability

### Backup & Recovery

```bash
# Database backup
docker-compose exec database pg_dump -U fpl_user fpl_data > backup.sql

# Restore from backup
docker-compose exec -T database psql -U fpl_user fpl_data < backup.sql
```

## 📚 Documentation

- [Architecture Overview](docs/data_collection_architecture.md)
- [API Documentation](docs/api_documentation.md)
- [Deployment Guide](docs/deployment_guide.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards

- Follow PEP 8 style guide
- Add type hints
- Write docstrings
- Include tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create GitHub issues for bugs and feature requests
- **Documentation**: Check the docs/ directory
- **Health Monitoring**: Use the built-in health checker
- **Logs**: Check Docker logs for debugging

## 🚀 Roadmap

- [ ] Real-time data streaming
- [ ] Machine learning integration
- [ ] Advanced analytics dashboard
- [ ] Mobile app support
- [ ] Additional data sources 