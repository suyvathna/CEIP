import { useState } from "react";
import { Outlet, Link as RouterLink, useNavigate } from "react-router-dom";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import SearchIcon from "@mui/icons-material/Search";
import LogoutIcon from "@mui/icons-material/Logout";
import ScheduleIcon from "@mui/icons-material/Schedule";
import NotificationBell from "./NotificationBell";
import { useAuth } from "../context/AuthContext";

function Layout() {
  const { loggedIn, logout } = useAuth();
  const navigate = useNavigate();
  const [searchValue, setSearchValue] = useState("");

  function handleSearchSubmit(e) {
    e.preventDefault();
    const trimmed = searchValue.trim();
    if (!trimmed) return;
    navigate(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar position="sticky" elevation={0}>
        <Toolbar sx={{ gap: 2, flexWrap: "wrap", py: 1 }}>
          <Typography
            component={RouterLink}
            to="/"
            variant="h6"
            sx={{
              fontWeight: 700,
              textDecoration: "none",
              color: "inherit",
              mr: 2,
            }}
          >
            CEIP
          </Typography>

          {loggedIn && (
            <Stack direction="row" spacing={1} sx={{ mr: "auto" }}>
              <Button component={RouterLink} to="/" size="small">
                Projects
              </Button>
              <Button
                component={RouterLink}
                to="/deadlines"
                size="small"
                startIcon={<ScheduleIcon fontSize="small" />}
              >
                Deadlines
              </Button>
            </Stack>
          )}

          {loggedIn && (
            <Box
              component="form"
              onSubmit={handleSearchSubmit}
              sx={{ flex: "1 1 260px", maxWidth: 420 }}
            >
              <TextField
                size="small"
                fullWidth
                placeholder="Search events, diaries, evidence…"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon fontSize="small" />
                      </InputAdornment>
                    ),
                  },
                }}
              />
            </Box>
          )}

          {/* Both engines write into one alert stream and this is the
              only place it surfaces globally - the bell turns red the
              moment anything rights-destroying (a Sub-Clause 20.2 notice
              period, a 3.7.5 NOD window, a 3.5 instruction notice) is
              inside its alert window. */}
          {loggedIn && <NotificationBell />}

          {loggedIn ? (
            <Button
              onClick={logout}
              size="small"
              variant="outlined"
              startIcon={<LogoutIcon fontSize="small" />}
            >
              Log Out
            </Button>
          ) : (
            <Button component={RouterLink} to="/login" size="small" variant="outlined">
              Log In
            </Button>
          )}
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Outlet />
      </Container>
    </Box>
  );
}

export default Layout;
