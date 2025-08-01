class AIService {
    constructor() {
        this.apiKey = process.env.REACT_APP_OPENAI_API_KEY || process.env.REACT_APP_ANTHROPIC_API_KEY;
        this.baseURL = 'https://api.openai.com/v1'; // or your preferred AI service
        
        if (!this.apiKey) {
            console.error('AI API key not found in environment variables');
        }
    }

    async generateTopics(text) {
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
            } catch (parseError) {
                // Fallback parsing if AI doesn't return valid JSON
                return this.parseTopicsFromText(content);
            }

        } catch (error) {
            console.error('Topic generation error:', error);
            throw {
                error: "Connection problem",
                details: error.message,
                user_action: "Please check your internet connection and API configuration.",
                error_code: "network_error"
            };
        }
    }

    async generateBullets(topicText) {
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
            } catch (parseError) {
                // Extract bullets from text if JSON parsing fails
                return this.extractBulletsFromText(content);
            }

        } catch (error) {
            console.error('Bullet generation error:', error);
            throw {
                error: "Connection problem",
                details: error.message,
                user_action: "Please check your internet connection and API configuration.",
                error_code: "network_error"
            };
        }
    }

    parseTopicsFromText(text) {
        // Fallback parser for non-JSON responses
        const topics = [];
        const lines = text.split('\n').filter(line => line.trim());
        
        let currentTopic = null;
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

    extractBulletsFromText(text) {
        const bullets = text.split('\n')
            .filter(line => line.match(/^[-*•]/))
            .map(line => line.replace(/^[-*•]\s*/, '').trim())
            .filter(bullet => bullet.length > 0);
        
        return bullets.length > 0 ? bullets : [text.trim()];
    }

    // Test connection method
    async testConnection() {
        try {
            const response = await fetch(`${this.baseURL}/models`, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`
                }
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

export default new AIService();
