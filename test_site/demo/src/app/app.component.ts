import { Component } from '@angular/core';
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
    </div>
  `,
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'demo';
  userName: string = '';
  greeting: string = '';

  onSubmit(): void {
    this.greeting = this.userName ? `Hello ${this.userName}, welcome to demo!!!` : '';
  }
}
