import type { Metadata, Viewport } from 'next';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'GezinsAI',
  description: 'De slimme gezinsplanner met AI',
  manifest: '/manifest.json',
};

export const viewport: Viewport = {
  themeColor: '#4A6741',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  );
}
