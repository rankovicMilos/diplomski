# Sector Risk Analysis — Frontend

A Next.js application for generating and viewing market position reports and peer analysis for banking clients.

## Features

- **File Upload**: Upload client financial data (PDF/Excel) for analysis
- **Market Analysis**: Generate sector-based market position reports with commodity breakdown
- **Peer Comparison**: Analyze client performance against industry peers
- **Data Visualization**: Interactive charts and tables for financial metrics
- **Document Export**: Export analysis reports to DOCX format
- **Search & Filter**: Find analyses by client name or category

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **UI**: Material-UI + Tailwind CSS
- **State**: React Query (TanStack Query)
- **Charts**: MUI X Charts
- **Backend**: AWS Lambda API (API Gateway)

## Getting Started

### Prerequisites

- Node.js 20+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Build

```bash
npm run build
npm start
```

## Project Structure

```
src/
├── app/                      # Next.js app router pages
│   ├── analysis/            # Analysis detail pages
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Home page
├── components/              # React components
│   ├── Analysis/            # Analysis display components
│   ├── DragAndDropFile/     # File upload
│   ├── Header/              # Navigation header
│   └── ...
├── hooks/                   # Custom React hooks
│   └── queries/             # React Query hooks
├── lib/                     # Core utilities
│   ├── api.ts               # API client & types
│   └── naceCategories.ts    # NACE sector codes
└── utils/                   # Helper functions
    └── generateClientPositionDocx.ts  # Document generation
```

## API Integration

### Configuration

The API base URLs are in `src/lib/apiUrl.ts`:

- `NEXT_PUBLIC_API_URL` — orchestrator API (default `http://localhost:8001`)
- `NEXT_PUBLIC_UPLOAD_API_URL` — upload API (default `http://localhost:8002`)

In `npm run dev` the browser calls `/api-proxy/*` on its own origin and `next.config.ts`
rewrites the requests to those services (`/upload` and `/local-upload/*` to the upload API,
everything else to the orchestrator), with a 10-minute proxy timeout for report generation.
A production build (`output: 'export'`) calls `NEXT_PUBLIC_API_URL` directly.

### Key Endpoints

- `GET /analyses` - List all market position analyses
- `GET /analyses/:category` - Get analysis by category
- `GET /analyses/client/:id` - Get client report (market position + peer analysis)
- `POST /analyses` - Generate new market position report
- `POST /upload` - Upload client data files
- `PUT /local-upload/<key>` - Local stand-in for the S3 presigned upload URL

## Key Dependencies

- **@mui/material** - Material-UI components
- **@tanstack/react-query** - Server state management
- **docx** - DOCX document generation
- **react-markdown** - Markdown rendering
- **nuqs** - URL state management

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
