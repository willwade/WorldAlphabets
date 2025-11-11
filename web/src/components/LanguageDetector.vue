<template>
  <div class="language-detector">
    <div class="detector-header">
      <h2>🔍 Language Detection</h2>
      <p class="detector-description">
        Test our frequency-based language detection system. Enter text in any language and see how accurately we can identify it!
      </p>
    </div>

    <div class="detector-input">
      <div class="input-section">
        <label for="detection-text" class="input-label">Enter text to detect:</label>
        <textarea
          id="detection-text"
          v-model="inputText"
          placeholder="Type or paste text in any language here..."
          class="text-input"
          rows="4"
          @input="onTextChange"
        ></textarea>
        
        <div class="input-actions">
          <button 
            @click="detectLanguage" 
            :disabled="!inputText.trim() || isDetecting"
            class="detect-btn"
          >
            {{ isDetecting ? '🔍 Analyzing...' : 'Detect Language' }}
          </button>
          <button @click="clearInput" class="clear-btn">Clear</button>
        </div>
      </div>

      <!-- Example texts -->
      <div class="examples-section">
        <h3>Try these examples:</h3>
        <div class="examples-grid">
          <button
            v-for="example in exampleTexts"
            :key="example.code"
            @click="useExample(example)"
            class="example-btn"
            :title="`${example.name} example`"
          >
            <span class="example-flag">{{ example.flag }}</span>
            <span class="example-text">{{ example.text }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="detectionResults.length > 0 || hasDetected" class="results-section">
      <h3>Detection Results</h3>
      
      <div v-if="isDetecting" class="loading-state">
        <div class="loading-spinner"></div>
        <div class="progress-info">
          <p>{{ detectionStatus }}</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: detectionProgress + '%' }"></div>
          </div>
          <div class="progress-stats">
            <span>{{ processedLanguages }}/{{ totalLanguages }} languages</span>
            <span v-if="detectionTimeElapsed > 0">{{ detectionTimeElapsed.toFixed(1) }}s elapsed</span>
          </div>
        </div>
      </div>
      
      <div v-else-if="detectionResults.length > 0" class="results-list">
        <div
          v-for="(result, index) in detectionResults"
          :key="result.language"
          class="result-item"
          :class="{ 'top-result': index === 0 }"
        >
          <div class="result-header">
            <span class="result-rank">#{{ index + 1 }}</span>
            <span class="result-language">{{ result.languageName }}</span>
            <span class="result-code">({{ result.language }})</span>
            <span class="result-confidence">{{ (result.confidence * 100).toFixed(1) }}%</span>
          </div>
          
          <div class="result-details">
            <span class="result-detail">{{ result.mode }} mode</span>
            <span class="result-detail">{{ result.tokenCount }} tokens</span>
            <span v-if="result.matchingTokens.length > 0" class="result-detail">
              Matches: {{ result.matchingTokens.slice(0, 5).join(', ') }}
              <span v-if="result.matchingTokens.length > 5">...</span>
            </span>
          </div>
        </div>
      </div>
      
      <div v-else-if="hasDetected" class="no-results">
        <p>No languages detected with sufficient confidence.</p>
        <p class="no-results-help">
          Try using longer text or text with more common words.
        </p>
      </div>
    </div>

    <!-- How it works -->
    <div class="how-it-works">
      <details>
        <summary>How does language detection work?</summary>
        <div class="explanation">
          <p>
            Our language detection system uses a <strong>hybrid approach</strong> combining
            word-based and character-based analysis:
          </p>
          <ul>
            <li><strong>Word-based detection (primary):</strong> Uses Top-200 frequency lists for 86 languages with available word data</li>
            <li><strong>Character-based fallback:</strong> Analyzes character sets and frequencies for languages without word data</li>
            <li><strong>Tokenization:</strong> Text is split into words, character bigrams, and individual characters</li>
            <li><strong>Scoring:</strong> Languages are scored based on word overlap or character analysis</li>
            <li><strong>Ranking:</strong> Results prioritize word-based detections while including character-based fallbacks</li>
          </ul>
          <p>
            The system supports <strong>{{ availableLanguages }} languages</strong> total: 86 with word frequency data
            (sourced from Leipzig Corpora, HermitDave FrequencyWords, and Tatoeba sentences) plus 245+ additional
            languages detected via character analysis using alphabet data.
          </p>
          <p>
            <a href="/docs/detect.md" target="_blank">Learn more about our detection system →</a>
          </p>
        </div>
      </details>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import languageDetectionService from '../services/languageDetectionServiceNew.js';

// Reactive data
const inputText = ref('');
const detectionResults = ref([]);
const isDetecting = ref(false);
const hasDetected = ref(false);
const availableLanguages = ref(0);

// Progress tracking
const detectionStatus = ref('');
const detectionProgress = ref(0);
const processedLanguages = ref(0);
const totalLanguages = ref(0);
const detectionTimeElapsed = ref(0);
const detectionStartTime = ref(0);

// Example texts for testing
const exampleTexts = ref([
  {
    code: 'de',
    name: 'German',
    flag: '🇩🇪',
    text: 'Ich bin sehr glücklich und ich habe viel Geld.'
  },
  {
    code: 'fr',
    name: 'French', 
    flag: '🇫🇷',
    text: 'Je suis très heureux et j\'ai beaucoup d\'argent.'
  },
  {
    code: 'es',
    name: 'Spanish',
    flag: '🇪🇸', 
    text: 'Estoy muy feliz y tengo mucho dinero.'
  },
  {
    code: 'ru',
    name: 'Russian',
    flag: '🇷🇺',
    text: 'Я очень счастлив и у меня много денег.'
  },
  {
    code: 'ar',
    name: 'Arabic',
    flag: '🇸🇦',
    text: 'أنا سعيد جداً ولدي الكثير من المال.'
  },
  {
    code: 'ko',
    name: 'Korean',
    flag: '🇰🇷',
    text: '나는 매우 행복하고 돈이 많이 있습니다.'
  },
  {
    code: 'af',
    name: 'Afrikaans',
    flag: '🇿🇦',
    text: 'Die man het die boek gelees en hy is baie gelukkig.'
  },
  {
    code: 'no',
    name: 'Norwegian',
    flag: '🇳🇴',
    text: 'Jeg er veldig lykkelig og jeg har mye penger.'
  }
]);

// Methods
const detectLanguage = async () => {
  if (!inputText.value.trim()) {
    console.log('No text to detect');
    return;
  }

  console.log('Starting language detection for:', inputText.value.trim());
  console.log('Service available languages:', languageDetectionService.getAvailableLanguages().length);

  // Initialize progress tracking
  isDetecting.value = true;
  hasDetected.value = false;
  detectionResults.value = [];
  detectionProgress.value = 0;
  processedLanguages.value = 0;
  totalLanguages.value = languageDetectionService.getAvailableLanguages().length;
  detectionStartTime.value = performance.now();
  detectionStatus.value = '🚀 Starting language detection...';

  // Show immediate feedback
  await new Promise(resolve => setTimeout(resolve, 100));
  detectionStatus.value = '📚 Loading language data...';
  detectionProgress.value = 5;

  // Start progress timer with more frequent updates
  const progressTimer = setInterval(() => {
    if (isDetecting.value) {
      detectionTimeElapsed.value = (performance.now() - detectionStartTime.value) / 1000;
    }
  }, 50);

  try {
    const results = await languageDetectionService.detectLanguages(
      inputText.value.trim(),
      null, // Use automatic candidate selection
      5,    // topK
      (progress) => {
        detectionStatus.value = progress.status;
        detectionProgress.value = progress.percentage;
        processedLanguages.value = progress.processed;
        totalLanguages.value = progress.total;
      }
    );

    console.log('Detection results:', results);
    console.log('Top 5 results:');
    results.slice(0, 5).forEach((r, i) => {
      console.log(`  ${i + 1}. ${r.languageName} (${r.language}): ${r.confidence.toFixed(4)} [${r.mode}]`);
    });
    detectionResults.value = results;
    hasDetected.value = true;
    detectionStatus.value = 'Detection complete!';
  } catch (error) {
    console.error('Detection failed:', error);
    detectionResults.value = [];
    hasDetected.value = true;
    detectionStatus.value = 'Detection failed';
  } finally {
    clearInterval(progressTimer);
    isDetecting.value = false;
  }
};

const clearInput = () => {
  inputText.value = '';
  detectionResults.value = [];
  hasDetected.value = false;
};

const useExample = (example) => {
  console.log('Using example:', example);
  inputText.value = example.text;
  // Auto-detect after setting example
  setTimeout(() => {
    console.log('Auto-detecting after example selection...');
    detectLanguage();
  }, 100);
};

const onTextChange = () => {
  // Clear previous results when text changes
  if (hasDetected.value) {
    detectionResults.value = [];
    hasDetected.value = false;
  }
};

// Initialize service on mount
onMounted(async () => {
  try {
    console.log('Initializing language detection service...');
    await languageDetectionService.initialize();
    availableLanguages.value = languageDetectionService.getAvailableLanguages().length;
    console.log(`Language detection initialized with ${availableLanguages.value} languages`);
  } catch (error) {
    console.error('Failed to initialize language detection:', error);
    // Set a fallback number so the UI still works
    availableLanguages.value = 86;
  }
});
</script>

<style scoped>
.language-detector {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.detector-header {
  text-align: center;
  margin-bottom: 2rem;
}

.detector-header h2 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.8rem;
}

.detector-description {
  color: #666;
  font-size: 1rem;
  line-height: 1.5;
  margin: 0;
}

.detector-input {
  margin-bottom: 2rem;
}

.input-section {
  margin-bottom: 2rem;
}

.input-label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.text-input {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
  transition: border-color 0.2s;
}

.text-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.input-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.detect-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.detect-btn:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
}

.detect-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
}

.clear-btn {
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: #e9ecef;
  color: #495057;
}

.examples-section h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.1rem;
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 0.75rem;
}

.example-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.example-btn:hover {
  background: #e9ecef;
  border-color: #007bff;
  transform: translateY(-1px);
}

.example-flag {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.example-text {
  font-size: 0.9rem;
  color: #495057;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.results-section {
  border-top: 1px solid #dee2e6;
  padding-top: 2rem;
}

.results-section h3 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.3rem;
}

.loading-state {
  padding: 2rem;
  text-align: center;
  color: #666;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  border: 2px solid #007bff;
  border-radius: 12px;
  margin: 1rem 0;
  animation: pulse-border 2s ease-in-out infinite;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #007bff;
  border-right: 5px solid #0056b3;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1.5rem;
}

.progress-info {
  max-width: 450px;
  margin: 0 auto;
}

.progress-info p {
  font-size: 1.1rem;
  font-weight: 500;
  color: #007bff;
  margin-bottom: 1rem;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background-color: #e9ecef;
  border-radius: 6px;
  overflow: hidden;
  margin: 1rem 0;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #0056b3, #007bff);
  background-size: 200% 100%;
  border-radius: 6px;
  transition: width 0.2s ease;
  animation: progress-shimmer 1.5s ease-in-out infinite;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #888;
  margin-top: 0.5rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes pulse-border {
  0%, 100% {
    border-color: #007bff;
    box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.4);
  }
  50% {
    border-color: #0056b3;
    box-shadow: 0 0 0 8px rgba(0, 123, 255, 0.1);
  }
}

@keyframes progress-shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-item {
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background: #f8f9fa;
  transition: all 0.2s;
}

.result-item.top-result {
  border-color: #28a745;
  background: #d4edda;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.result-rank {
  background: #007bff;
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 2rem;
  text-align: center;
}

.top-result .result-rank {
  background: #28a745;
}

.result-language {
  font-weight: 600;
  color: #333;
  font-size: 1.1rem;
}

.result-code {
  color: #6c757d;
  font-size: 0.9rem;
}

.result-confidence {
  margin-left: auto;
  background: #007bff;
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 600;
}

.top-result .result-confidence {
  background: #28a745;
}

.result-details {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.85rem;
  color: #6c757d;
}

.result-detail {
  background: white;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
}

.no-results-help {
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.how-it-works {
  margin-top: 2rem;
  border-top: 1px solid #dee2e6;
  padding-top: 1.5rem;
}

.how-it-works summary {
  cursor: pointer;
  font-weight: 600;
  color: #007bff;
  padding: 0.5rem 0;
}

.how-it-works summary:hover {
  color: #0056b3;
}

.explanation {
  padding: 1rem 0;
  color: #495057;
  line-height: 1.6;
}

.explanation ul {
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.explanation li {
  margin-bottom: 0.5rem;
}

.explanation a {
  color: #007bff;
  text-decoration: none;
}

.explanation a:hover {
  text-decoration: underline;
}

/* Responsive design */
@media (max-width: 768px) {
  .language-detector {
    padding: 1.5rem;
  }
  
  .detector-header h2 {
    font-size: 1.5rem;
  }
  
  .examples-grid {
    grid-template-columns: 1fr;
  }
  
  .input-actions {
    flex-direction: column;
  }
  
  .result-header {
    flex-wrap: wrap;
  }
  
  .result-details {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
