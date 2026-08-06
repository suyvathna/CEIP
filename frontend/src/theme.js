import { createTheme } from "@mui/material/styles";

// "Field register" palette: cool drafting-paper ground, deep survey-ink
// text, laterite red-orange as the one accent (the colour of the road
// subgrade soil these highway contracts are literally built on), muted
// brass as a secondary marker. Mirrors the same tokens in index.css so
// the MUI surfaces (AppBar, dashboards, tables, forms) and the legacy
// plain-CSS pages (project/event CRUD, login) read as one system.
// Semantic status colours (error/warning/success/info) are deliberately
// distinct from the primary accent hue, not shades of it.
const theme = createTheme({
  palette: {
    primary: {
      main: "#b8481f",
      dark: "#963b19",
      light: "#d97a48",
      contrastText: "#ffffff",
    },
    secondary: {
      main: "#8c6a22",
      dark: "#6f5419",
      contrastText: "#ffffff",
    },
    error: {
      main: "#a02b2b",
    },
    warning: {
      main: "#8a5e12",
    },
    success: {
      main: "#2e6a4a",
    },
    info: {
      main: "#33566b",
    },
    background: {
      default: "#edf0ef",
      paper: "#ffffff",
    },
    text: {
      primary: "#16232c",
      secondary: "#57666e",
    },
    divider: "#d6dcda",
    severity: {
      low: "#2e6a4a",
      medium: "#8a5e12",
      high: "#a02b2b",
    },
  },
  shape: {
    borderRadius: 4,
  },
  typography: {
    fontFamily: "'Barlow', system-ui, 'Segoe UI', Roboto, sans-serif",
    h1: { fontFamily: "'Barlow Condensed', sans-serif", fontWeight: 700, letterSpacing: "0.01em" },
    h2: { fontFamily: "'Barlow Condensed', sans-serif", fontWeight: 700, letterSpacing: "0.01em" },
    h3: { fontFamily: "'Barlow Condensed', sans-serif", fontWeight: 700, letterSpacing: "0.01em" },
    h4: { fontFamily: "'Barlow Condensed', sans-serif", fontWeight: 700, letterSpacing: "0.01em" },
    h5: { fontFamily: "'Barlow Condensed', sans-serif", fontWeight: 600, letterSpacing: "0.01em" },
    h6: { fontFamily: "'Barlow Condensed', sans-serif", fontWeight: 600, letterSpacing: "0.01em" },
    subtitle1: { fontWeight: 500 },
    subtitle2: { fontWeight: 600 },
    // Table headers, chip labels and the like read as technical register
    // captions when they get the eyebrow treatment - condensed, uppercase,
    // a touch of tracking - rather than plain small grey text.
    overline: {
      fontFamily: "'Barlow Condensed', sans-serif",
      fontWeight: 600,
      letterSpacing: "0.09em",
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "#ffffff",
          color: "#16232c",
          borderBottom: "1px solid #d6dcda",
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 500,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          border: "1px solid #d6dcda",
          backgroundImage: "none",
        },
      },
      defaultProps: {
        elevation: 0,
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontFamily: "'Barlow Condensed', sans-serif",
          fontWeight: 600,
          fontSize: "0.7rem",
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          color: "#57666e",
          backgroundColor: "#e4e8e7",
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          backgroundColor: "#b8481f",
          height: 2,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 500,
          "&.Mui-selected": {
            color: "#b8481f",
          },
        },
      },
    },
  },
});

export default theme;

export const severityColor = (severity) => {
  switch (severity) {
    case "High":
      return "error";
    case "Medium":
      return "warning";
    default:
      return "success";
  }
};

export const statusColor = (status) => {
  return status === "Open" ? "warning" : "success";
};

export const projectStatusColor = (status) => {
  switch (status) {
    case "Planning":
      return "default";
    case "In Progress":
      return "info";
    case "On Hold":
      return "warning";
    case "Completed":
      return "success";
    default:
      return "default";
  }
};

export const directionColor = (direction) => {
  return direction === "Outgoing" ? "primary" : "secondary";
};

export const noticeStatusColor = (noticeStatus) => {
  switch (noticeStatus) {
    case "overdue":
      return "error";
    case "given_late":
      return "warning";
    case "given_on_time":
      return "success";
    default:
      return "info";
  }
};
