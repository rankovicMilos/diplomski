import { createTheme, ThemeOptions } from '@mui/material/styles';

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: '#fee600',
      light: '#fff492',
      dark: '#eacd00',
      contrastText: '#000000',
    },
    secondary: {
      main: '#67d0ab',
      light: '#b6ecd9',
      dark: '#39b287',
      contrastText: '#ffffff',
    },
    error: {
      main: '#d32f2f',
    },
    warning: {
      main: '#ed6c02',
    },
    info: {
      main: '#0288d1',
    },
    success: {
      main: '#2e7d32',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    grey: {
      "900": '#000000'
    },
  },

  typography: {
    fontFamily: '"Amalia", "Arial", "Helvetica", "sans-serif"',
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {

      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
        },
      },
      defaultProps: {
        disableElevation: true,
        variant: "contained"
      },
    },
    MuiTextField: {
      defaultProps: {
        color: "secondary",
      }
    },
    MuiSelect:{
      defaultProps: {
        color: "secondary",
        
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          marginTop: "16px",
          marginBottom: "16px"
        }
      }
    },
    MuiCssBaseline: {
      styleOverrides: {
        h1: {
          fontSize: '2rem' ,
          lineHeight: '2.5rem',
          fontWeight: 700,
        },
        h2: {
          fontSize: '1.5rem' ,
          lineHeight: '2.5rem',
          fontWeight: 500,
        },
        h3: {
          fontSize: '1.25rem',
          fontWeight: 500,
        },
        h4: {
          fontSize: '1.125rem',
          fontWeight: 500,
        },
        p: {
          fontSize: '1rem',
          lineHeight: '1.25rem'
        },
        th: {
          padding: '1rem',
          textAlign: 'center'
        },
        td: {
          padding: '1rem',
          textAlign: 'center'
        }
      }
    }
  },
};

const theme = createTheme(themeOptions);

export default theme;