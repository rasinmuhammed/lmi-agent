import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './global.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'LMI Agent - Labor Market Intelligence',
  description: 'AI-powered skill gap analysis and labor market insights based on real job data',
  keywords: ['job search', 'skill analysis', 'career development', 'AI', 'machine learning'],
  authors: [{ name: 'Your Name' }],
  openGraph: {
    title: 'LMI Agent - Labor Market Intelligence',
    description: 'Get data-driven insights into job market trends and skill requirements',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}