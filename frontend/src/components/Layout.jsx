import { useState } from "react";
import { Outlet, Link as RouterLink, useMatch, useNavigate } from "react-router-dom";
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
import NotificationBell from "./NotificationBell";
import { useAuth } from "../context/AuthContext";

function Layout() {
  const { loggedIn, logout } = useAuth();
  const navigate = useNavigate();
  const [searchValue, setSearchValue] = useState("");

  // Everything in this app is scoped to one project - there is no
  // cross-project view anywhere, including search and alerts. Layout
  // wraps every route (project and non-project alike), so it has to know
  // whether the current route is inside a project to decide whether to
  // show either at all. "/projects/new" matches this pattern too (its
  // "projectId" slot is literally the word "new"), so that's excluded -
  // it isn't a real project.
  const projectMatch = useMatch("/projects/:projectId/*");
  const matchedProjectId = projectMatch?.params?.projectId;
  const activeProjectId =
    matchedProjectId && matchedProjectId !== "new" ? matchedProjectId : null;

  function handleSearchSubmit(e) {
    e.preventDefault();
    const trimmed = searchValue.trim();
    if (!trimmed || !activeProjectId) return;
    navigate(`/projects/${activeProjectId}/search?q=${encodeURIComponent(trimmed)}`);
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
            </Stack>
          )}

          {loggedIn && activeProjectId && (
            <Box
              component="form"
              onSubmit={handleSearchSubmit}
              sx={{ flex: "1 1 260px", maxWidth: 420 }}
            >
              <TextField
                size="small"
                fullWidth
                placeholder="Search this project's events, diaries, evidence…"
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

          {/* Both engines write into one alert stream, scoped to whichever
              project is currently open - never shown mixed across
              projects, so it only renders at all while inside one. */}
          {loggedIn && activeProjectId && (
            <NotificationBell projectId={activeProjectId} />
          )}

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
