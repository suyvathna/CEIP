import { createTheme } from "@mui/material/styles";

// Mirrors the green palette that was already defined in index.css so the
// new MUI surfaces (AppBar, Dashboard, Timeline, Report, Search) sit
// naturally next to the legacy plain-CSS pages that are kept as-is.
const theme = createTheme({
  palette: {
    primary: {
      main: "#2f6f4f",
      dark: "#255a40",
      contrastText: "#ffffff",
    },
    error: {
      main: "#b3261e",
    },
    background: {
      default: "#f7f7f8",
      paper: "#ffffff",
    },
    text: {
      primary: "#1f2023",
      secondary: "#6b6b74",
    },
    severity: {
      low: "#1f6b3a",
      medium: "#8a6100",
      high: "#a3231c",
    },
  },
  shape: {
    borderRadius: 8,
  },
  typography: {
    fontFamily: "system-ui, 'Segoe UI', Roboto, sans-serif",
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "#ffffff",
          color: "#1f2023",
          borderBottom: "1px solid #e2e2e6",
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
          border: "1px solid #e2e2e6",
        },
      },
      defaultProps: {
        elevation: 0,
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
