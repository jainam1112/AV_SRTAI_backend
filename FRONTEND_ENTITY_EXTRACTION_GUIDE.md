# Frontend Integration Guide: Entity Extraction API

## Overview
This guide provides complete frontend integration instructions for the enhanced entity extraction API that extracts 8 different types of entities from spiritual discourse transcripts.

## API Endpoint Details

### Entity Extraction Endpoint
```
POST /transcripts/{transcript_name}/extract-entities
```

**Parameters:**
- `transcript_name` (path parameter): Name of the transcript to process
- Request body (optional): JSON configuration object

**Request Body Schema:**
```typescript
interface EntityExtractionRequest {
  use_ai?: boolean;              // Default: true (use AI extraction vs rule-based)
  include_statistics?: boolean;  // Default: true (include detailed statistics)
}
```

**Response Schema:**
```typescript
interface EntityExtractionResponse {
  status: "success" | "error";
  transcript_name: string;
  chunks_processed: number;
  chunks_updated: number;
  method_used: "AI" | "rule-based";
  entity_statistics?: EntityStatistics;
}

interface EntityStatistics {
  total_chunks: number;
  chunks_with_entities: number;
  self_reference_chunks: number;
  entity_counts: {
    people: number;
    places: number;
    concepts: number;
    scriptures: number;
    dates: number;
    organizations: number;
    events: number;
    objects: number;
  };
  unique_entities: {
    people: string[];
    places: string[];
    concepts: string[];
    scriptures: string[];
    dates: string[];
    organizations: string[];
    events: string[];
    objects: string[];
  };
}
```

## Frontend Implementation Examples

### React Component Example

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const EntityExtractionComponent = ({ transcriptName }) => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [useAI, setUseAI] = useState(true);
  const [includeStats, setIncludeStats] = useState(true);

  const extractEntities = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(
        `http://localhost:10000/transcripts/${transcriptName}/extract-entities`,
        {
          use_ai: useAI,
          include_statistics: includeStats
        }
      );
      
      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to extract entities');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="entity-extraction-panel">
      <h3>Entity Extraction for: {transcriptName}</h3>
      
      {/* Configuration Options */}
      <div className="extraction-options">
        <label>
          <input
            type="checkbox"
            checked={useAI}
            onChange={(e) => setUseAI(e.target.checked)}
          />
          Use AI Extraction (more accurate but slower)
        </label>
        
        <label>
          <input
            type="checkbox"
            checked={includeStats}
            onChange={(e) => setIncludeStats(e.target.checked)}
          />
          Include detailed statistics
        </label>
      </div>

      {/* Extract Button */}
      <button 
        onClick={extractEntities} 
        disabled={loading}
        className="extract-btn"
      >
        {loading ? 'Extracting Entities...' : 'Extract Entities'}
      </button>

      {/* Results Display */}
      {results && (
        <div className="extraction-results">
          <div className="summary">
            <h4>Extraction Summary</h4>
            <p>Status: {results.status}</p>
            <p>Method: {results.method_used}</p>
            <p>Chunks Processed: {results.chunks_processed}</p>
            <p>Chunks Updated: {results.chunks_updated}</p>
          </div>

          {results.entity_statistics && (
            <div className="statistics">
              <h4>Entity Statistics</h4>
              <div className="stats-grid">
                <div className="stat-card">
                  <h5>Overview</h5>
                  <p>Total Chunks: {results.entity_statistics.total_chunks}</p>
                  <p>Chunks with Entities: {results.entity_statistics.chunks_with_entities}</p>
                  <p>Self-Reference Chunks: {results.entity_statistics.self_reference_chunks}</p>
                </div>

                <div className="stat-card">
                  <h5>Entity Counts</h5>
                  {Object.entries(results.entity_statistics.entity_counts).map(([type, count]) => (
                    <p key={type}>{type}: {count}</p>
                  ))}
                </div>

                <div className="stat-card">
                  <h5>Unique Entities Found</h5>
                  {Object.entries(results.entity_statistics.unique_entities).map(([type, entities]) => (
                    entities.length > 0 && (
                      <div key={type}>
                        <strong>{type}:</strong>
                        <ul>
                          {entities.slice(0, 5).map((entity, idx) => (
                            <li key={idx}>{entity}</li>
                          ))}
                          {entities.length > 5 && <li>... and {entities.length - 5} more</li>}
                        </ul>
                      </div>
                    )
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <p>Error: {error}</p>
        </div>
      )}
    </div>
  );
};

export default EntityExtractionComponent;
```

### Vue.js Component Example

```vue
<template>
  <div class="entity-extraction-panel">
    <h3>Entity Extraction for: {{ transcriptName }}</h3>
    
    <!-- Configuration Options -->
    <div class="extraction-options">
      <label>
        <input v-model="useAI" type="checkbox" />
        Use AI Extraction (more accurate but slower)
      </label>
      
      <label>
        <input v-model="includeStats" type="checkbox" />
        Include detailed statistics
      </label>
    </div>

    <!-- Extract Button -->
    <button @click="extractEntities" :disabled="loading" class="extract-btn">
      {{ loading ? 'Extracting Entities...' : 'Extract Entities' }}
    </button>

    <!-- Results Display -->
    <div v-if="results" class="extraction-results">
      <div class="summary">
        <h4>Extraction Summary</h4>
        <p>Status: {{ results.status }}</p>
        <p>Method: {{ results.method_used }}</p>
        <p>Chunks Processed: {{ results.chunks_processed }}</p>
        <p>Chunks Updated: {{ results.chunks_updated }}</p>
      </div>

      <div v-if="results.entity_statistics" class="statistics">
        <h4>Entity Statistics</h4>
        <div class="stats-grid">
          <div class="stat-card">
            <h5>Overview</h5>
            <p>Total Chunks: {{ results.entity_statistics.total_chunks }}</p>
            <p>Chunks with Entities: {{ results.entity_statistics.chunks_with_entities }}</p>
            <p>Self-Reference Chunks: {{ results.entity_statistics.self_reference_chunks }}</p>
          </div>

          <div class="stat-card">
            <h5>Entity Counts</h5>
            <p v-for="(count, type) in results.entity_statistics.entity_counts" :key="type">
              {{ type }}: {{ count }}
            </p>
          </div>

          <div class="stat-card">
            <h5>Unique Entities Found</h5>
            <div v-for="(entities, type) in results.entity_statistics.unique_entities" :key="type">
              <div v-if="entities.length > 0">
                <strong>{{ type }}:</strong>
                <ul>
                  <li v-for="(entity, idx) in entities.slice(0, 5)" :key="idx">{{ entity }}</li>
                  <li v-if="entities.length > 5">... and {{ entities.length - 5 }} more</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="error-message">
      <p>Error: {{ error }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'EntityExtractionComponent',
  props: {
    transcriptName: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      loading: false,
      results: null,
      error: null,
      useAI: true,
      includeStats: true
    };
  },
  methods: {
    async extractEntities() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post(
          `http://localhost:10000/transcripts/${this.transcriptName}/extract-entities`,
          {
            use_ai: this.useAI,
            include_statistics: this.includeStats
          }
        );
        
        this.results = response.data;
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to extract entities';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

### Vanilla JavaScript Example

```javascript
class EntityExtractionAPI {
  constructor(baseURL = 'http://localhost:10000') {
    this.baseURL = baseURL;
  }

  async extractEntities(transcriptName, options = {}) {
    const {
      useAI = true,
      includeStatistics = true
    } = options;

    try {
      const response = await fetch(
        `${this.baseURL}/transcripts/${transcriptName}/extract-entities`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            use_ai: useAI,
            include_statistics: includeStatistics
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to extract entities');
      }

      return await response.json();
    } catch (error) {
      console.error('Entity extraction failed:', error);
      throw error;
    }
  }
}

// Usage example
const entityAPI = new EntityExtractionAPI();

async function runEntityExtraction(transcriptName) {
  try {
    const results = await entityAPI.extractEntities(transcriptName, {
      useAI: true,
      includeStatistics: true
    });
    
    console.log('Extraction completed:', results);
    displayResults(results);
  } catch (error) {
    console.error('Error:', error.message);
    displayError(error.message);
  }
}

function displayResults(results) {
  const container = document.getElementById('results-container');
  
  container.innerHTML = `
    <div class="extraction-results">
      <h4>Extraction Summary</h4>
      <p>Status: ${results.status}</p>
      <p>Method: ${results.method_used}</p>
      <p>Chunks Processed: ${results.chunks_processed}</p>
      <p>Chunks Updated: ${results.chunks_updated}</p>
      
      ${results.entity_statistics ? `
        <h4>Entity Statistics</h4>
        <p>Total Chunks: ${results.entity_statistics.total_chunks}</p>
        <p>Chunks with Entities: ${results.entity_statistics.chunks_with_entities}</p>
        <p>Self-Reference Chunks: ${results.entity_statistics.self_reference_chunks}</p>
        
        <h5>Entity Counts</h5>
        ${Object.entries(results.entity_statistics.entity_counts)
          .map(([type, count]) => `<p>${type}: ${count}</p>`)
          .join('')}
          
        <h5>Unique Entities</h5>
        ${Object.entries(results.entity_statistics.unique_entities)
          .filter(([type, entities]) => entities.length > 0)
          .map(([type, entities]) => `
            <div>
              <strong>${type}:</strong>
              <ul>
                ${entities.slice(0, 5).map(entity => `<li>${entity}</li>`).join('')}
                ${entities.length > 5 ? `<li>... and ${entities.length - 5} more</li>` : ''}
              </ul>
            </div>
          `).join('')}
      ` : ''}
    </div>
  `;
}
```

### Angular Component Example

```typescript
// entity-extraction.component.ts
import { Component, Input } from '@angular/core';
import { HttpClient } from '@angular/common/http';

interface EntityExtractionRequest {
  use_ai?: boolean;
  include_statistics?: boolean;
}

interface EntityExtractionResponse {
  status: string;
  transcript_name: string;
  chunks_processed: number;
  chunks_updated: number;
  method_used: string;
  entity_statistics?: any;
}

@Component({
  selector: 'app-entity-extraction',
  template: `
    <div class="entity-extraction-panel">
      <h3>Entity Extraction for: {{ transcriptName }}</h3>
      
      <div class="extraction-options">
        <label>
          <input type="checkbox" [(ngModel)]="useAI" />
          Use AI Extraction (more accurate but slower)
        </label>
        
        <label>
          <input type="checkbox" [(ngModel)]="includeStats" />
          Include detailed statistics
        </label>
      </div>

      <button (click)="extractEntities()" [disabled]="loading" class="extract-btn">
        {{ loading ? 'Extracting Entities...' : 'Extract Entities' }}
      </button>

      <div *ngIf="results" class="extraction-results">
        <div class="summary">
          <h4>Extraction Summary</h4>
          <p>Status: {{ results.status }}</p>
          <p>Method: {{ results.method_used }}</p>
          <p>Chunks Processed: {{ results.chunks_processed }}</p>
          <p>Chunks Updated: {{ results.chunks_updated }}</p>
        </div>

        <div *ngIf="results.entity_statistics" class="statistics">
          <h4>Entity Statistics</h4>
          <p>Total Chunks: {{ results.entity_statistics.total_chunks }}</p>
          <p>Chunks with Entities: {{ results.entity_statistics.chunks_with_entities }}</p>
          <p>Self-Reference Chunks: {{ results.entity_statistics.self_reference_chunks }}</p>
          
          <h5>Entity Counts</h5>
          <div *ngFor="let item of getEntityCounts()">
            <p>{{ item.type }}: {{ item.count }}</p>
          </div>
        </div>
      </div>

      <div *ngIf="error" class="error-message">
        <p>Error: {{ error }}</p>
      </div>
    </div>
  `
})
export class EntityExtractionComponent {
  @Input() transcriptName!: string;
  
  loading = false;
  results: EntityExtractionResponse | null = null;
  error: string | null = null;
  useAI = true;
  includeStats = true;

  constructor(private http: HttpClient) {}

  async extractEntities() {
    this.loading = true;
    this.error = null;
    
    const request: EntityExtractionRequest = {
      use_ai: this.useAI,
      include_statistics: this.includeStats
    };

    try {
      this.results = await this.http.post<EntityExtractionResponse>(
        `http://localhost:10000/transcripts/${this.transcriptName}/extract-entities`,
        request
      ).toPromise();
    } catch (err: any) {
      this.error = err.error?.detail || 'Failed to extract entities';
    } finally {
      this.loading = false;
    }
  }

  getEntityCounts() {
    if (!this.results?.entity_statistics?.entity_counts) return [];
    
    return Object.entries(this.results.entity_statistics.entity_counts)
      .map(([type, count]) => ({ type, count }));
  }
}
```

## CSS Styles

```css
.entity-extraction-panel {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
}

.extraction-options {
  margin: 15px 0;
}

.extraction-options label {
  display: block;
  margin: 8px 0;
  cursor: pointer;
}

.extract-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.extract-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.extraction-results {
  margin-top: 20px;
  padding: 15px;
  background: white;
  border-radius: 4px;
}

.summary {
  margin-bottom: 20px;
  padding: 10px;
  background: #e7f3ff;
  border-radius: 4px;
}

.statistics {
  padding: 10px;
  background: #f0f8f0;
  border-radius: 4px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-top: 10px;
}

.stat-card {
  padding: 15px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.stat-card h5 {
  margin-top: 0;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

.stat-card ul {
  margin: 10px 0;
  padding-left: 20px;
}

.error-message {
  margin-top: 15px;
  padding: 10px;
  background: #ffe6e6;
  color: #d00;
  border: 1px solid #ffcccc;
  border-radius: 4px;
}
```

## Integration Checklist

### Before Implementation:
- [ ] Ensure backend server is running on http://localhost:10000
- [ ] Verify CORS is properly configured for your frontend domain
- [ ] Test API endpoint with Postman or curl
- [ ] Confirm OpenAI API key is configured for AI extraction

### Implementation Steps:
1. [ ] Install HTTP client library (axios, fetch, etc.)
2. [ ] Create entity extraction component
3. [ ] Add proper TypeScript interfaces/types
4. [ ] Implement error handling
5. [ ] Add loading states and user feedback
6. [ ] Style the component appropriately
7. [ ] Test with sample transcript data
8. [ ] Add integration to your main application

### Testing:
- [ ] Test with both AI and rule-based extraction
- [ ] Verify statistics display correctly
- [ ] Test error handling for invalid transcript names
- [ ] Check loading states and user experience
- [ ] Validate entity data is properly stored in Qdrant

## Entity Types Extracted

The system extracts 8 different types of entities:

1. **People**: Names of individuals mentioned (spiritual teachers, historical figures, etc.)
2. **Places**: Locations referenced (cities, countries, spiritual sites, etc.)
3. **Concepts**: Spiritual and philosophical concepts (meditation, dharma, etc.)
4. **Scriptures**: Religious texts and books mentioned
5. **Dates**: Temporal references and special occasions
6. **Organizations**: Groups, institutions, and spiritual organizations
7. **Events**: Ceremonies, festivals, and significant happenings
8. **Objects**: Physical or conceptual items mentioned

This comprehensive entity extraction enhances the searchability and analytical capabilities of your spiritual discourse platform.
