import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import IconButton from "@mui/material/IconButton";
import Badge from "@mui/material/Badge";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Tooltip from "@mui/material/Tooltip";
import NotificationsIcon from "@mui/icons-material/Notifications";
import EngineChip from "./EngineChip";
import {
  getNotifications,
  getNotificationSummary,
  markAllNotificationsRead,
  markNotificationRead,
} from "../api/notifications";

const SEVERITY_COLORS = {
  Critical: "error",
  Warning: "warning",
  Info: "info",
};

const CATEGORY_LABELS = {
  Compliance: "Compliance",
  Claim: "Claim",
  Determination: "Determination",
  Variation: "Variation",
  Event: "Event",
};

// 60s. The engines write on a daily sweep plus on user actions, so
// anything faster is polling for changes that structurally can't have
// happened; anything much slower and a colleague logging an unlabelled
// instruction on site wouldn't surface here until the PM reloaded.
const REFETCH_MS = 60_000;

function NotificationBell() {
  const [anchorEl, setAnchorEl] = useState(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const summaryQuery = useQuery({
    queryKey: ["notificationSummary"],
    queryFn: () => getNotificationSummary(),
    refetchInterval: REFETCH_MS,
  });

  const listQuery = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => getNotifications({ unreadOnly: true, limit: 20 }),
    enabled: Boolean(anchorEl),
  });

  const readMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
    },
  });

  const readAllMutation = useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notificationSummary"] });
    },
  });

  const summary = summaryQuery.data || { total: 0, critical: 0 };
  const notifications = listQuery.data || [];

  function handleOpen(event) {
    setAnchorEl(event.currentTarget);
  }

  function handleClose() {
    setAnchorEl(null);
  }

  function handleSelect(notification) {
    readMutation.mutate(notification.id);
    handleClose();
    if (notification.link_path) navigate(notification.link_path);
  }

  return (
    <>
      <Tooltip
        title={
          summary.critical > 0
            ? `${summary.critical} deadline(s) that forfeit an entitlement if missed`
            : "Contract deadlines and alerts"
        }
      >
        <IconButton onClick={handleOpen} size="small" color="inherit">
          {/* Red the moment anything rights-destroying is open. A badge
              reading "12" means something very different depending on
              whether any of them are time-bars, so the colour carries
              that and the count doesn't have to. */}
          <Badge
            badgeContent={summary.total}
            color={summary.critical > 0 ? "error" : "primary"}
            max={99}
          >
            <NotificationsIcon fontSize="small" />
          </Badge>
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        slotProps={{ paper: { sx: { width: 460, maxHeight: 520 } } }}
      >
        <Box sx={{ px: 2, py: 1.5 }}>
          <Stack
            direction="row"
            sx={{ justifyContent: "space-between", alignItems: "center" }}
          >
            <Typography variant="subtitle1" fontWeight={700}>
              Alerts
            </Typography>
            <Button
              size="small"
              onClick={() => readAllMutation.mutate()}
              disabled={notifications.length === 0 || readAllMutation.isPending}
            >
              Mark all read
            </Button>
          </Stack>
          {summary.critical > 0 && (
            <Typography variant="caption" color="error" display="block">
              {summary.critical} of these forfeit an entitlement if missed.
            </Typography>
          )}
          {/* The split matters more than the total: five routine
              submissions and five running time-bars are very different
              mornings. */}
          <Typography variant="caption" color="text.secondary">
            {summary.engine_a || 0} routine compliance (A) ·{" "}
            {summary.engine_b || 0} event-driven clocks (B)
          </Typography>
        </Box>

        <Divider />

        {listQuery.isLoading && (
          <MenuItem disabled>
            <Typography variant="body2">Loading…</Typography>
          </MenuItem>
        )}

        {!listQuery.isLoading && notifications.length === 0 && (
          <MenuItem disabled sx={{ whiteSpace: "normal" }}>
            <Typography variant="body2" color="text.secondary">
              Nothing outstanding. Alerts clear themselves as soon as the
              thing they were about is recorded, waived or re-dated, so an
              empty bell means genuinely nothing is due — not that nobody
              has looked.
            </Typography>
          </MenuItem>
        )}

        {notifications.map((notification) => (
          <MenuItem
            key={notification.id}
            onClick={() => handleSelect(notification)}
            sx={{ whiteSpace: "normal", alignItems: "flex-start", py: 1.25 }}
            divider
          >
            <Stack spacing={0.5} sx={{ width: "100%" }}>
              <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: "center", flexWrap: "wrap" }}
              >
                <Chip
                  size="small"
                  color={SEVERITY_COLORS[notification.severity] || "default"}
                  label={notification.severity}
                />
                <EngineChip engine={notification.engine} />
                <Chip
                  size="small"
                  variant="outlined"
                  label={
                    CATEGORY_LABELS[notification.category] ||
                    notification.category
                  }
                />
                {notification.days_remaining !== null &&
                  notification.days_remaining !== undefined && (
                    <Typography variant="caption" color="text.secondary">
                      {notification.days_remaining < 0
                        ? `${Math.abs(notification.days_remaining)} day(s) overdue`
                        : `${notification.days_remaining} day(s) left`}
                    </Typography>
                  )}
              </Stack>

              <Typography variant="body2" fontWeight={600}>
                {notification.title}
              </Typography>

              {notification.body && (
                <Typography variant="caption" color="text.secondary">
                  {notification.body}
                </Typography>
              )}
            </Stack>
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}

export default NotificationBell;
