interface AITopic {
  title: string;
  bullets: string[];
}

interface AITopicsResponse {
  topics: AITopic[];
}

interface AIError {
  error: string;
  details: string;
  user_action: string;
  error_code: string;
}

class AIService {
  private apiKey: string | undefined;
  private baseURL: string;

  constructor() {
    this.apiKey = import.meta.env.REACT_APP_OPENAI_API_KEY || import.meta.env.REACT_APP_ANTHROPIC_API_KEY;
    this.baseURL = 'https://api.openai.com/v1'; // or your preferred AI service
    
    if (!this.apiKey) {
      console.error('AI API key not found in environment variables');
    }
  }

  async generateTopics(text: string): Promise<AITopicsResponse> {
    try {
      if (!text || text.trim().length < 50) {
        throw new Error('Insufficient text content for topic generation');
      }

      const response = await fetch(`${this.baseURL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: 'gpt-3.5-turbo',
          messages: [{
            role: 'user',
            content: `Analyze the following text and generate 3-5 main topics with bullet points for each topic. Format as JSON:

Text: ${text}

Return format:
{
  "topics": [
    {
      "title": "Topic Name",
      "bullets": ["Bullet 1", "Bullet 2", "Bullet 3"]
    }
  ]
}`
          }],
          max_tokens: 1000,
          temperature: 0.7
        })
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      const content = data.choices[0].message.content;
      
      try {
        return JSON.parse(content);
      } catch {
        // Fallback parsing if AI doesn't return valid JSON
        return this.parseTopicsFromText(content);
      }

    } catch (error) {
      console.error('Topic generation error:', error);
      const aiError: AIError = {
        error: "Connection problem",
        details: error instanceof Error ? error.message : 'Unknown error',
        user_action: "Please check your internet connection and API configuration.",
        error_code: "network_error"
      };
      throw aiError;
    }
  }

  async generateBullets(topicText: string): Promise<string[]> {
    try {
      if (!topicText || topicText.trim().length < 20) {
        throw new Error('Insufficient text content for bullet generation');
      }

      const response = await fetch(`${this.baseURL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: 'gpt-3.5-turbo',
          messages: [{
            role: 'user',
            content: `Generate 3-5 concise bullet points from this text:

${topicText}

Return as a JSON array: ["bullet 1", "bullet 2", "bullet 3"]`
          }],
          max_tokens: 300,
          temperature: 0.5
        })
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();
      const content = data.choices[0].message.content;
      
      try {
        return JSON.parse(content);
      } catch {
        // Extract bullets from text if JSON parsing fails
        return this.extractBulletsFromText(content);
      }

    } catch (error) {
      console.error('Bullet generation error:', error);
      const aiError: AIError = {
        error: "Connection problem",
        details: error instanceof Error ? error.message : 'Unknown error',
        user_action: "Please check your internet connection and API configuration.",
        error_code: "network_error"
      };
      throw aiError;
    }
  }

  private parseTopicsFromText(text: string): AITopicsResponse {
    // Fallback parser for non-JSON responses
    const topics: AITopic[] = [];
    const lines = text.split('\n').filter(line => line.trim());
    
    let currentTopic: AITopic | null = null;
    for (const line of lines) {
      if (line.match(/^\d+\.|^#|^##/)) {
        if (currentTopic) topics.push(currentTopic);
        currentTopic = {
          title: line.replace(/^\d+\.|^#+\s*/, '').trim(),
          bullets: []
        };
      } else if (line.match(/^[-*•]/)) {
        if (currentTopic) {
          currentTopic.bullets.push(line.replace(/^[-*•]\s*/, '').trim());
        }
      }
    }
    
    if (currentTopic) topics.push(currentTopic);
    return { topics };
  }

  private extractBulletsFromText(text: string): string[] {
    const bullets = text.split('\n')
      .filter(line => line.match(/^[-*•]/))
      .map(line => line.replace(/^[-*•]\s*/, '').trim())
      .filter(bullet => bullet.length > 0);
    
    return bullets.length > 0 ? bullets : [text.trim()];
  }

  // Test connection method
  async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/models`, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

export default new AIService();
