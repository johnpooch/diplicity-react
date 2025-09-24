import React, { createContext, useContext } from 'react';

export const theme = {
  colors: {
    primary: '#007AFF',
    secondary: '#5856D6',
    background: '#FFFFFF',
    surface: '#F2F2F7',
    text: '#000000',
    textSecondary: '#8E8E93',
    border: '#C6C6C8',
    success: '#34C759',
    warning: '#FF9500',
    error: '#FF3B30',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  typography: {
    title: { fontSize: 20, fontWeight: 'bold' as const },
    body: { fontSize: 16, fontWeight: 'normal' as const },
    caption: { fontSize: 14, fontWeight: 'normal' as const },
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 16,
  },
} as const;

export type Theme = typeof theme;

const ThemeContext = createContext<Theme>(theme);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  return (
    <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
