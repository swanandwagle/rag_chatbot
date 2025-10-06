
# RAG Chat Web Component

A reusable, framework-agnostic chat interface for RAG (Retrieval-Augmented Generation) systems. Built with React, packaged as a Web Component for universal compatibility.

## ✨ Features

- 🔌 **Plug & Play**: Works in Angular, React, Vue, or vanilla JavaScript
- 🎨 **Modern UI**: Clean, responsive chat interface with source citations
- 🚀 **Zero Dependencies**: Single JavaScript file, no npm install needed
- 📦 **Lightweight**: ~200KB minified (including React runtime)
- 🎯 **Framework Agnostic**: Standard Web Component API
- 💬 **Real-time Chat**: Streaming responses supported
- 📚 **Source Citations**: Shows document sources with similarity scores
- 🔗 **Backend Agnostic**: Works with any RAG API endpoint

## 🚀 Quick Start

### Option 1: Direct File Copy (Recommended)

1. **Build the component**:
   ```bash
   cd frontend
   npm install
   npm run build:webcomponent
   ```

2. **Copy output files** to your app:
   ```
   dist/webcomponent/rag-chat.js    → your-app/src/assets/
   dist/webcomponent/rag-chat.css   → your-app/src/assets/
   ```

3. **Use in any framework** (see integration guides below)

### Option 2: Development Mode

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to see the standalone demo.

## 📖 Integration Guides

### Angular Integration

**Step 1**: Copy files to `src/assets/`

**Step 2**: Load in `src/index.html`:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Your App</title>
  <base href="/">
  <link rel="stylesheet" href="assets/rag-chat.css">
</head>
<body>
  <app-root></app-root>
  <script src="assets/rag-chat.js"></script>
</body>
</html>
```

**Step 3**: Add schema to `app.module.ts`:
```typescript
import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';

@NgModule({
  declarations: [AppComponent],
  imports: [BrowserModule],
  schemas: [CUSTOM_ELEMENTS_SCHEMA], // Add this
  bootstrap: [AppComponent]
})
export class AppModule { }
```

**Step 4**: Use in any component template:
```html
<!-- chat.component.html -->
<div class="chat-container">
  <rag-chat-interface
    api-url="http://localhost:8000/api/v1"
    title="Document Q&A"
    (rag-error)="handleError($event)">
  </rag-chat-interface>
</div>
```

```typescript
// chat.component.ts
import { Component } from '@angular/core';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent {
  handleError(event: any) {
    console.error('Chat error:', event.detail);
  }
}
```

```css
/* chat.component.css */
.chat-container {
  width: 100%;
  max-width: 900px;
  height: 800px;
  margin: 0 auto;
}
```

### React Integration

**Step 1**: Copy files to `public/`

**Step 2**: Load in `public/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>React App</title>
    <link rel="stylesheet" href="%PUBLIC_URL%/rag-chat.css">
  </head>
  <body>
    <div id="root"></div>
    <script src="%PUBLIC_URL%/rag-chat.js"></script>
  </body>
</html>
```

**Step 3**: Use in components:
```tsx
// ChatPage.tsx
import React, { useRef, useEffect } from 'react';

const ChatPage: React.FC = () => {
  const chatRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handleError = (event: any) => {
      console.error('Chat error:', event.detail);
    };

    const element = chatRef.current;
    if (element) {
      element.addEventListener('rag-error', handleError);
      return () => element.removeEventListener('rag-error', handleError);
    }
  }, []);

  return (
    <div style={{ width: '900px', height: '800px', margin: '0 auto' }}>
      <rag-chat-interface
        ref={chatRef as any}
        api-url="http://localhost:8000/api/v1"
        title="Document Q&A"
      />
    </div>
  );
};

export default ChatPage;
```

**TypeScript support**: Add to `react-app-env.d.ts`:
```typescript
declare namespace JSX {
  interface IntrinsicElements {
    'rag-chat-interface': any;
  }
}
```

### Vue Integration

**Step 1**: Copy files to `public/`

**Step 2**: Load in `public/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Vue App</title>
    <link rel="stylesheet" href="<%= BASE_URL %>rag-chat.css">
  </head>
  <body>
    <div id="app"></div>
    <script src="<%= BASE_URL %>rag-chat.js"></script>
  </body>
</html>
```

**Step 3**: Use in components:
```vue
<template>
  <div class="chat-container">
    <rag-chat-interface
      :api-url="apiUrl"
      title="Document Q&A"
      @rag-error="handleError"
    />
  </div>
</template>

<script>
export default {
  name: 'ChatPage',
  data() {
    return {
      apiUrl: 'http://localhost:8000/api/v1'
    };
  },
  methods: {
    handleError(event) {
      console.error('Chat error:', event.detail);
    }
  }
};
</script>

<style scoped>
.chat-container {
  width: 900px;
  height: 800px;
  margin: 0 auto;
}
</style>
```

**Vue 3 TypeScript**: Add to `shims-vue.d.ts`:
```typescript
declare module '@vue/runtime-core' {
  export interface GlobalComponents {
    'rag-chat-interface': any;
  }
}
```

### Vanilla JavaScript

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RAG Chat</title>
  <link rel="stylesheet" href="rag-chat.css">
  <style>
    body {
      margin: 0;
      padding: 20px;
      font-family: system-ui, -apple-system, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .container {
      width: 100%;
      max-width: 900px;
      height: 800px;
    }
  </style>
</head>
<body>
  <div class="container">
    <rag-chat-interface
      api-url="http://localhost:8000/api/v1"
      title="Document Q&A Assistant"
    ></rag-chat-interface>
  </div>

  <script src="rag-chat.js"></script>
  <script>
    // Listen for errors
    const chatElement = document.querySelector('rag-chat-interface');
    chatElement.addEventListener('rag-error', (event) => {
      console.error('Chat error:', event.detail);
      alert('An error occurred: ' + event.detail.error);
    });
  </script>
</body>
</html>
```

## 🎛️ API Reference

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `api-url` | string | `http://localhost:8000/api/v1` | Backend API base URL |
| `title` | string | `RAG Chat Assistant` | Chat interface title |
| `placeholder` | string | `Ask a question...` | Input placeholder text |

### Events

| Event | Detail | Description |
|-------|--------|-------------|
| `rag-error` | `{ error: string }` | Fired when an error occurs |

### Methods

Currently, the component is controlled via attributes. Future versions may expose methods for programmatic control.

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```env
VITE_API_URL=http://localhost:8000/api/v1
```

### Build Configuration

The `vite.config.ts` is configured to output a single-file bundle in IIFE format, perfect for web components.

## 📦 Build Outputs

```
dist/
├── webcomponent/          # For distribution
│   ├── rag-chat.js       # Main bundle (~200KB minified)
│   ├── rag-chat.css      # Styles (~10KB)
│   └── rag-chat.js.map   # Source map
│
└── standalone/            # Standalone React app
    ├── index.html
    └── assets/
```

## 🛠️ Development

### Project Structure

```
frontend/
├── src/
│   ├── components/              # React components
│   │   ├── ChatInterface.tsx    # Main component
│   │   ├── ChatInterface.css
│   │   ├── MessageList.tsx
│   │   ├── MessageInput.tsx
│   │   ├── Message.tsx
│   │   └── SourceCard.tsx
│   ├── services/                # API client
│   │   ├── api.ts
│   │   └── types.ts
│   ├── webcomponent/            # Web component wrapper
│   │   ├── ChatWebComponent.tsx
│   │   └── index.ts
│   ├── App.tsx                  # Standalone demo
│   └── index.tsx
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### NPM Scripts

```bash
npm run dev                  # Start dev server (standalone mode)
npm run build               # Build standalone React app
npm run build:webcomponent  # Build web component (for distribution)
npm run preview             # Preview production build
npm run type-check          # TypeScript type checking
```

### Testing Locally

1. Start backend:
   ```bash
   cd backend
   python run.py
   ```

2. Start frontend dev server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open `http://localhost:5173`

## 🚢 Distribution Strategy

### For 20+ Apps

**Option A: Internal CDN**
```html
<script src="https://cdn.yourcompany.com/rag-chat/v1/rag-chat.js"></script>
<link rel="stylesheet" href="https://cdn.yourcompany.com/rag-chat/v1/rag-chat.css">
```

**Option B: Manual Copy**
- Build once
- Distribute `dist/webcomponent/*` to teams
- Teams copy to their `assets/` or `public/` folders

**Option C: NPM Private Registry**
```bash
npm publish --registry=https://npm.yourcompany.com
```

Then teams:
```bash
npm install @yourcompany/rag-chat-component
```

## 🔒 Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Any browser supporting Web Components v1

## 📝 License

MIT

## 🤝 Contributing

1. Make changes in `src/`
2. Test in standalone mode: `npm run dev`
3. Build web component: `npm run build:webcomponent`
4. Test in target framework (Angular/React/Vue)
5. Submit PR

## 🐛 Troubleshooting

### "Custom element not defined"
- Ensure `rag-chat.js` is loaded before using the component
- Check browser console for errors

### Styles not applied
- Verify `rag-chat.css` is loaded
- Check for CSS conflicts with host app

### CORS errors
- Backend must allow requests from your frontend origin
- Check `CORS_ORIGINS` in backend `.env`

### TypeScript errors in Angular
- Add `CUSTOM_ELEMENTS_SCHEMA` to your module
- Update `tsconfig.json` with `"skipLibCheck": true`

## 📞 Support

For issues or questions, please contact the development team or create an issue in the repository.

---

**Built with ❤️ using React, TypeScript, and Web Components**
