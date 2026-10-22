'use client';

import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from '@/theme'; // your theme file
import EmotionRegistry from './EmotionRegistry';

const ThemeWrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <EmotionRegistry>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </EmotionRegistry>
  );
};

export default ThemeWrapper;