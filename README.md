# FPL Chase API 🏃‍♂️

**The Backend Engine for FPL Hype Index**

*"Empower Your Gut Feelings"*

---

## About FPL Chase

**FPL Chase** is the powerful backend API that powers **FPL Hype Index** - the ultimate platform for validating your FPL instincts with data-driven insights.

Every FPL manager knows the feeling: you're watching a match, and suddenly a player catches your eye. Maybe it's a midfielder making dangerous runs, a defender with perfect positioning, or a forward with that "something special." Your gut screams, **"This is the guy!"**

But then the doubt creeps in. Should you trust your instinct, or should you rely on the cold, hard data?

**FPL Hype Index** doesn't make you choose. We empower your gut feelings with the data to back them up.

---

## The Brand Philosophy: Data-Driven Intuition

### The Eternal FPL Debate: "The Eye Test vs. The Algorithm"

- **The Eye Test:** "I watched the game, and Player X looked electric. He was everywhere, making dangerous runs. I have a good feeling about him."
- **The Algorithm:** "Player X has an xG of 0.12, faces three top-tier defenses next, and has a high rotation risk. Do not buy."

**FPL Hype Index** resolves this conflict beautifully. We don't say, "Your gut is wrong." We say, **"You have a hunch? Let's prove it."**

Your tool becomes the ultimate validation engine. It's the Iron Man suit for the FPL manager: your instinct is still in control, but it's amplified and supercharged by powerful data.

---

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FPL Hype      │    │   FPL Chase     │    │   Data Sources  │
│   Index         │◄──►│   API           │◄──►│   (FPL, etc.)   │
│   (Frontend)    │    │   (Backend)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User          │    │   Prediction    │    │   PostgreSQL    │
│   Interface     │    │   Engine        │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### FPL Chase API (This Repository)
- **RESTful API** - Complete backend services for FPL data and predictions
- **Prediction Engine** - Advanced Player Impact Score (PIS) calculations
- **Data Collection** - Automated FPL data scraping and processing
- **Transfer Optimization** - Intelligent transfer recommendations
- **Redis Caching** - Performance optimization for computed features

### FPL Hype Index (Frontend Platform)
- **Analytics Dashboard** - Visual insights and player comparisons
- **Team Analysis** - Personalized squad recommendations
- **Hype Tracking** - Monitor player popularity vs. performance
- **Transfer Planner** - Interactive transfer optimization tools

---

## Core Features

### 🎯 Player Impact Score (PIS)
Our proprietary algorithm that breaks down player performance into five key components:
- **Advanced Quality Score (35%)** - Underlying performance metrics
- **Form Consistency Score (25%)** - Recent performance trends
- **Team Momentum Score (15%)** - Team's overall form
- **Fixture Score (15%)** - Upcoming fixture difficulty
- **Value Score (10%)** - Price-to-performance ratio

### 🔄 Transfer Optimizer
Find the optimal transfer combinations that maximize your squad's potential while respecting FPL constraints.

### 📊 Hype Index Validation
Compare your gut feelings with data-driven insights:
- **Gut Check Score** - How well your instincts align with the data
- **Reality Check** - Hype vs. actual underlying stats
- **Decision Validation** - Confirmation that your transfer makes sense

### 🎮 Team Analysis
Get personalized insights for your specific FPL team:
- Current squad performance breakdown
- Position-specific recommendations
- Budget optimization suggestions
- Risk assessment and mitigation

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd fpl-chase

# Start the services
docker compose up -d

# The API will be available at http://localhost:8001
```

### API Usage Example
```bash
# Get player PIS scores
curl -X GET "http://localhost:8001/api/v1/prediction/scores/player/123"

# Get transfer recommendations
curl -X POST "http://localhost:8001/api/v1/prediction/transfers/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": 2165234,
    "strategy": "balanced",
    "max_transfers": 2
  }'

# Analyze your FPL team
python scripts/fpl_team_transfer_calculator.py
```

---

## API Endpoints

### Prediction Endpoints
- `GET /api/v1/prediction/scores/player/{player_id}` - Get player PIS score
- `POST /api/v1/prediction/transfers/recommendations` - Get transfer recommendations
- `GET /api/v1/prediction/team/{team_id}/analysis` - Analyze FPL team
- `POST /api/v1/prediction/backtest` - Run backtesting analysis

### Data Endpoints
- `GET /api/v1/data/players` - Get all players
- `GET /api/v1/data/teams` - Get all teams
- `GET /api/v1/data/fixtures` - Get fixtures
- `GET /api/v1/data/player/{player_id}/stats` - Get player statistics

### Health & Monitoring
- `GET /health` - API health check
- `GET /api/v1/status` - System status
- `GET /api/v1/metrics` - Performance metrics

---

## The FPL Hype Index Promise

**We believe the ultimate FPL manager is a powerful combination of human passion and machine intelligence.**

- **Respect Your Instincts** - Your football knowledge and intuition are invaluable
- **Validate with Data** - We provide the evidence to back up your hunches
- **Empower Your Decisions** - Make confident transfers with both heart and head
- **Improve Your Game** - Learn from the data while staying true to your instincts

---

## Data Flow Architecture

### 1. Data Collection Layer
- **FPL API** - Official Fantasy Premier League data
- **PostgreSQL** - Primary data storage for players, stats, fixtures
- **Automated Scraping** - Daily data updates and processing

### 2. Prediction Engine
- **Player Impact Score** - Multi-factor player evaluation algorithm
- **Transfer Optimization** - Constraint-based transfer recommendation engine
- **Backtesting Framework** - Historical performance validation
- **Risk Assessment** - Injury, rotation, and ownership risk analysis

### 3. API Layer
- **FastAPI** - High-performance RESTful API
- **Redis Cache** - 1-day caching for predictions and computed features
- **Rate Limiting** - API protection and fair usage
- **Authentication** - Secure access control

### 4. Integration Layer
- **FPL Hype Index Frontend** - Web-based analytics platform
- **Mobile Apps** - iOS/Android applications
- **Third-party Tools** - Integration with existing FPL tools

---

## Development

### Project Structure
```
fpl-chase/
├── api/                   # FastAPI application
├── prediction/            # Prediction engine
│   ├── scoring/          # PIS algorithms
│   ├── optimization/     # Transfer optimization
│   └── validation/       # Backtesting framework
├── storage/              # Database models and access
├── scrapers/             # Data collection
├── utils/                # Common utilities
├── scripts/              # Utility scripts
└── tests/                # Test suite
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server
uvicorn api.main:app --reload --port 8001
```

---

## Contributing

We welcome contributions that align with our philosophy of empowering FPL managers' instincts with data-driven insights.

### Development Guidelines
- Follow PEP 8 style guide
- Add type hints and docstrings
- Include tests for new features
- Update API documentation
- Respect the "Empower Your Gut Feelings" philosophy

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Connect With Us

- **FPL Hype Index**: [fplhypeindex.com](https://fplhypeindex.com)
- **Twitter**: [@FPLHypeIndex](https://twitter.com/FPLHypeIndex)
- **Discord**: [FPL Hype Index Community](https://discord.gg/fpl-hype-index)

---

**Remember: Trust your gut. We'll handle the numbers.** 🎯

*"Empower Your Gut Feelings"*

---

**FPL Chase API** - The powerful backend engine for **FPL Hype Index** 🏃‍♂️ 