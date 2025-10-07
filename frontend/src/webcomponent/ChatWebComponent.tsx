
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChatInterface, ChatInterfaceProps } from '../components/ChatInterface';

/**
 * Web Component wrapper for ChatInterface
 * This allows the React component to be used in ANY framework (Angular, Vue, vanilla JS)
 */
export class ChatWebComponent extends HTMLElement {
  private root: ReactDOM.Root | null = null;
  private mountPoint: HTMLDivElement | null = null;

  // Observed attributes - these will trigger attributeChangedCallback
  static get observedAttributes() {
    return ['api-url', 'title', 'placeholder'];
  }

  constructor() {
    super();
    // Create shadow DOM for style encapsulation (optional)
    // Uncomment if you want complete style isolation
    // this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    // Called when element is added to the DOM
    this.mountPoint = document.createElement('div');
    this.mountPoint.style.height = '100%';
    this.mountPoint.style.width = '100%';
    
    // Append to shadow DOM or regular DOM
    // If using shadow DOM: this.shadowRoot!.appendChild(this.mountPoint);
    this.appendChild(this.mountPoint);
    
    this.render();
  }

  disconnectedCallback() {
    // Called when element is removed from the DOM
    if (this.root) {
      this.root.unmount();
      this.root = null;
    }
  }

  attributeChangedCallback(name: string, oldValue: string, newValue: string) {
    // Called when observed attributes change
    void name; // mark as used to satisfy TS when not referenced directly
    if (oldValue !== newValue) {
      this.render();
    }
  }

  private getProps(): ChatInterfaceProps {
    return {
      apiUrl: this.getAttribute('api-url') || undefined,
      title: this.getAttribute('title') || undefined,
      placeholder: this.getAttribute('placeholder') || undefined,
      onError: (error) => {
        // Dispatch custom event for error handling
        this.dispatchEvent(new CustomEvent('rag-error', {
          detail: { error: error.message },
          bubbles: true,
          composed: true
        }));
      }
    };
  }

  private render() {
    if (!this.mountPoint) return;

    if (!this.root) {
      this.root = ReactDOM.createRoot(this.mountPoint);
    }

    const props = this.getProps();
    this.root.render(React.createElement(ChatInterface, props));
  }
}

