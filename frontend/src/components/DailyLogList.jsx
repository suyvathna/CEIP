import { Link as RouterLink } from "react-router-dom";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Chip from "@mui/material/Chip";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import PhotoCameraIcon from "@mui/icons-material/PhotoCamera";
import GroupsIcon from "@mui/icons-material/Groups";

function DailyLogList({ projectId, dailyLogs }) {
  if (dailyLogs.length === 0) {
    return (
      <Typography color="text.secondary">
        No Daily Log entries recorded yet.
      </Typography>
    );
  }

  return (
    <Stack spacing={1.5}>
      {dailyLogs.map((dailyLog) => {
        const weatherDelay = (dailyLog.weather_observations || []).some(
          (o) => o.caused_delay
        );

        return (
          <Card key={dailyLog.id} variant="outlined">
            <CardActionArea
              component={RouterLink}
              to={`/projects/${projectId}/daily-log/${dailyLog.id}`}
            >
              <CardContent>
                <Stack
                  direction="row"
                  sx={{
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                    gap: 1,
                  }}
                >
                  <Typography variant="subtitle1" fontWeight={600}>
                    {dailyLog.diary_date}
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {weatherDelay && (
                      <Chip
                        size="small"
                        color="warning"
                        icon={<WarningAmberIcon />}
                        label="Weather delay"
                      />
                    )}
                    {dailyLog.total_workers > 0 && (
                      <Chip
                        size="small"
                        variant="outlined"
                        icon={<GroupsIcon />}
                        label={`${dailyLog.total_workers} workers`}
                      />
                    )}
                    {dailyLog.photo_count > 0 && (
                      <Chip
                        size="small"
                        variant="outlined"
                        icon={<PhotoCameraIcon />}
                        label={dailyLog.photo_count}
                      />
                    )}
                    {dailyLog.linked_event_ids?.length > 0 && (
                      <Chip
                        size="small"
                        variant="outlined"
                        label={`${dailyLog.linked_event_ids.length} linked event${
                          dailyLog.linked_event_ids.length === 1 ? "" : "s"
                        }`}
                      />
                    )}
                  </Stack>
                </Stack>
                {dailyLog.work_completed && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    <strong>Work:</strong> {dailyLog.work_completed}
                  </Typography>
                )}
                {dailyLog.delays && (
                  <Typography variant="body2" color="text.secondary">
                    <strong>Delays:</strong> {dailyLog.delays}
                  </Typography>
                )}
              </CardContent>
            </CardActionArea>
          </Card>
        );
      })}
    </Stack>
  );
}

export default DailyLogList;
