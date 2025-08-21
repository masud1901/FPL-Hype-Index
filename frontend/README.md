# 🎮 FPL Hype Index Frontend

**"Empower Your Gut Feelings" - The Pixel Art FPL Experience**

---

## 🎯 About

FPL Hype Index is a unique, pixel art-styled Fantasy Premier League tool that validates your gut feelings with data-driven insights. Built with Next.js, TypeScript, and custom pixel art styling.

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- FPL Chase API running on `http://localhost:8001`

### Installation
```bash
# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

---

## 🛠️ Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Custom Pixel Art CSS
- **Animations**: Framer Motion
- **Fonts**: Press Start 2P, VT323, Silkscreen
- **HTTP Client**: Axios
- **State Management**: React Hooks

---

## 🎨 Pixel Art Design System

### Colors
- **Green** (#00ff00) - Success, good gut feelings
- **Red** (#ff0000) - Warnings, reality checks  
- **Yellow** (#ffff00) - Caution, mixed signals
- **Blue** (#0000ff) - Information, data
- **Purple** (#ff00ff) - Premium features

### Typography
- **Titles**: Press Start 2P (arcade style)
- **Subtitles**: VT323 (terminal style)
- **Body**: Silkscreen (clean pixel font)

### Components
- **PixelButton** - Animated buttons with hover effects
- **PixelCard** - Content containers with pixel borders
- **PixelProgressBar** - Score visualization
- **PixelInput** - Search and form inputs

---

## 📁 Project Structure

```
src/
├── app/                 # Next.js App Router
│   ├── globals.css     # Global pixel art styles
│   └── page.tsx        # Main landing page
├── components/         # Reusable pixel art components
│   ├── PixelButton.tsx
│   ├── PixelCard.tsx
│   └── PixelProgressBar.tsx
└── lib/               # Utilities and API
    └── api.ts         # FPL Chase API integration
```

---

## 🔌 API Integration

The frontend communicates with the **FPL Chase API** (your backend) through:

- **Health Check**: `/health`
- **Player Search**: `/api/v1/data/players?search=`
- **Player Scores**: `/api/v1/prediction/scores/player/{id}`
- **Transfer Recommendations**: `/api/v1/prediction/transfers/recommendations`
- **Team Analysis**: `/api/v1/prediction/team/{id}/analysis`

---

## 🎮 Features

### Current Features
- ✅ **Player Search** - Find players by name
- ✅ **Gut Check Results** - Validate your instincts with data
- ✅ **Hype Index Display** - Visual score representation
- ✅ **Pixel Art UI** - Unique retro gaming aesthetic
- ✅ **Responsive Design** - Works on all devices

### Planned Features
- 🔄 **Team Analysis** - Squad-wide gut feeling validation
- 🔄 **Transfer Recommendations** - Smart transfer suggestions
- 🔄 **Community Features** - Share and compare gut feelings
- 🔄 **Advanced Analytics** - Detailed player breakdowns

---

## 🎯 User Experience

### The Gut Check Flow
1. **User has a hunch** about a player
2. **Searches for the player** using the pixel art interface
3. **Gets instant validation** with Hype Index score
4. **Receives insights** explaining why their gut was right/wrong
5. **Can dive deeper** for more detailed analysis

### Design Philosophy
- **Conversational** - Feels like talking to a smart FPL friend
- **Empowering** - Validates instincts, doesn't dismiss them
- **Fun** - Pixel art makes data approachable
- **Fast** - Instant results and smooth animations

---

## 🚀 Development

### Available Scripts
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Environment Variables
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001  # FPL Chase API URL
```

---

## 🎨 Customization

### Adding New Pixel Art Components
1. Create component in `src/components/`
2. Add styles to `src/app/globals.css`
3. Use Framer Motion for animations
4. Follow the pixel art design system

### Modifying Colors
Update CSS variables in `src/app/globals.css`:
```css
:root {
  --pixel-green: #00ff00;
  --pixel-red: #ff0000;
  /* ... other colors */
}
```

---

## 🔧 Troubleshooting

### Common Issues
- **API Connection Failed**: Ensure FPL Chase API is running on port 8001
- **Fonts Not Loading**: Check that `@fontsource` packages are installed
- **Styling Issues**: Verify Tailwind CSS is properly configured

### Debug Mode
Add `NODE_ENV=development` to see detailed error messages.

---

## 🏆 The Vision

**FPL Hype Index** will be the most memorable and effective FPL tool ever created by combining:

- **🎮 Nostalgic Pixel Art** - Unique and shareable
- **🎯 Data-Driven Insights** - Powerful backend analysis
- **💪 Empowering Philosophy** - Respects user instincts
- **🚀 Modern Technology** - Fast, responsive, scalable

---

*"Trust your gut. We'll handle the pixels."* 🎮

---

**Built with ❤️ for the FPL community**
