import { TopicResponse } from '../services/apiService';
import { NestedExpansions } from '../hooks/uploadPipelineTypes';

function normalizeBulletKey(bulletPoint: string): string {
  return bulletPoint.replace(/^[-*+]\s*/, '').trim().slice(0, 80);
}

function safeFilenameDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function sanitizeMarkdownLine(text: string): string {
  return text.replace(/[\r\n]+/g, ' ').trim();
}

export function exportAsMarkdown(topics: TopicResponse | null, expandedBullets: NestedExpansions): string {
  const lines: string[] = [];
  lines.push('# Firmament Notes');
  lines.push('');
  lines.push(`Generated: ${new Date().toLocaleString()}`);
  lines.push('');

  if (!topics || Object.keys(topics.topics).length === 0) {
    lines.push('No topics available.');
    return lines.join('\n');
  }

  for (const [topicId, topic] of Object.entries(topics.topics)) {
    const safeHeading = sanitizeMarkdownLine(topic.heading || `Topic ${topicId}`);
    lines.push(`## ${safeHeading}`);
    lines.push('');

    const bullets = topic.bullet_points && topic.bullet_points.length > 0 ? topic.bullet_points : topic.examples;

    if (!bullets || bullets.length === 0) {
      lines.push('- No bullet points available.');
      lines.push('');
      continue;
    }

    for (const bullet of bullets) {
      const safeBullet = sanitizeMarkdownLine(bullet);
      lines.push(`- ${safeBullet}`);

      const rootKey = `${topicId}_${normalizeBulletKey(bullet)}`;
      const expansion = expandedBullets[rootKey];

      if (expansion?.expansion?.expanded_bullets?.length) {
        for (const expanded of expansion.expansion.expanded_bullets) {
          lines.push(`  - ${sanitizeMarkdownLine(expanded)}`);
        }
      }

      if (expansion?.subExpansions) {
        for (const subExpansion of Object.values(expansion.subExpansions)) {
          if (!subExpansion.expansion.expanded_bullets?.length) continue;

          for (const subBullet of subExpansion.expansion.expanded_bullets) {
            lines.push(`    - ${sanitizeMarkdownLine(subBullet)}`);
          }
        }
      }
    }

    lines.push('');
  }

  return lines.join('\n').trimEnd() + '\n';
}

export function downloadMarkdown(markdown: string, filename: string = `firmament-notes-${safeFilenameDate()}.md`): void {
  if (typeof window === 'undefined') return;

  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');

  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

export async function copyToClipboard(markdown: string): Promise<boolean> {
  if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(markdown);
      return true;
    } catch {
      // Fallback path below.
    }
  }

  if (typeof document === 'undefined') {
    return false;
  }

  try {
    const textArea = document.createElement('textarea');
    textArea.value = markdown;
    textArea.setAttribute('readonly', '');
    textArea.style.position = 'absolute';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);

    textArea.select();
    textArea.setSelectionRange(0, textArea.value.length);
    const copied = document.execCommand('copy');

    document.body.removeChild(textArea);
    return copied;
  } catch {
    return false;
  }
}
