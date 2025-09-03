# World Alphabets Web UI

A Vue 3 + Vite web application for exploring world alphabets with advanced search, filtering, and data visualization capabilities.

## Features

### Alphabet Index Page
- **Comprehensive Search**: Search through 3000+ alphabets by name, language code, or script type
- **Advanced Filtering**: Filter alphabets by available features:
  - Text-to-Speech (TTS) availability
  - Frequency data availability
  - Keyboard layout availability
  - Script type (Latin, Cyrillic, Arabic, etc.)
- **Responsive Data Table**: View alphabet details including:
  - Language name and ISO codes
  - Script type and letter count
  - Available features with visual badges
- **Pagination**: Navigate through large result sets efficiently
- **Sorting**: Sort by name, language code, script, or letter count

### Language Explorer
- **Interactive Language List**: Browse languages with search functionality
- **Detailed Alphabet View**: Explore individual alphabets with:
  - Letter frequency visualization
  - Audio pronunciation (when available)
  - Keyboard layout information

## Technical Implementation

### Data Integration
- Combines multiple data sources:
  - `index.json`: Core alphabet metadata
  - `tts_index.json`: Text-to-speech availability
  - `kbdlayouts.json`: Keyboard layout information
- Client-side data enrichment and correlation
- Efficient caching and performance optimization

### Architecture
- **Vue 3** with Composition API
- **Vue Router** for navigation
- **Vite** for build tooling
- **Static Site Generation** for GitHub Pages deployment
- **Responsive Design** with mobile-first approach

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Routes

- `/` - Alphabet Index (browse and search all alphabets)
- `/explore` - Language Explorer (original interface)
- `/explore/:langCode` - Specific language details

## Data Sources

The application uses JSON data files located in `public/data/`:
- Alphabet definitions and metadata
- TTS voice availability by language
- Keyboard layout mappings
- Audio files for pronunciation

## Browser Support

Modern browsers with ES6+ support. Optimized for:
- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
