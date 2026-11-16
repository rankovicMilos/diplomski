import { createTheme, ThemeOptions } from '@mui/material/styles';

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: '#4F46E5',
      light: '#8B8AF5',
      dark: '#3730A3',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#4F46E5',
      light: '#8B8AF5',
      dark: '#3730A3',
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
      default: 'transparent',
      paper: 'rgba(255,255,255,0.6)',
    },
    grey: {
      "900": '#000000'
    },
  },

  typography: {
    fontFamily: 'var(--font-geist-sans), "Segoe UI", Arial, sans-serif',
  },
  shape: {
    borderRadius: 14,
  },
  components: {
    MuiButton: {

      styleOverrides: {
        root: {
          borderRadius: 999,
          padding: '8px 22px',
          textTransform: 'none',
          fontWeight: 600,
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
          boxShadow: '0 8px 32px rgba(31,38,135,0.10)',
          backdropFilter: 'blur(20px) saturate(180%)',
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: { backgroundColor: 'rgba(255,255,255,0.6)', borderRadius: 14 },
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