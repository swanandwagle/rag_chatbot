import { Component, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="landing">
      <h1>Enter your name</h1>
      <form (ngSubmit)="onSubmit()">
        <input
          type="text"
          name="name"
          [(ngModel)]="userName"
          placeholder="Your name"
        />
        <button type="submit">Submit</button>
      </form>
      <p class="greeting">{{ greeting }}</p>

      <h2>Embedded RAG Chat</h2>
      <!-- Web Component from frontend/dist/webcomponent/rag-chat.iife.js -->
      <rag-chat-interface
        api-url="http://localhost:8000/api/v1"
        title="RAG Chat Assistant"
        placeholder="Ask about your documents...">
      </rag-chat-interface>
    </div>
  `,
  styleUrl: './app.component.css'
  ,
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class AppComponent {
  title = 'demo';
  userName: string = '';
  greeting: string = '';

  onSubmit(): void {
    this.greeting = this.userName ? `Hello ${this.userName}, welcome to demo!!!` : '';
  }
}
