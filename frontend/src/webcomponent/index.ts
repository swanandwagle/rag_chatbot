
import { ChatWebComponent } from './ChatWebComponent';

// Register the custom element
if (!customElements.get('rag-chat-interface')) {
  customElements.define('rag-chat-interface', ChatWebComponent);
}

// Export for programmatic usage
export { ChatWebComponent };

