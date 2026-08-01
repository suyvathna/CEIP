import { Link as RouterLink } from "react-router-dom";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Chip from "@mui/material/Chip";
import { severityColor, statusColor } from "../theme";

function EventList({ projectId, events }) {
  if (events.length === 0) {
    return (
      <Typography color="text.secondary">No events recorded yet.</Typography>
    );
  }

  return (
    <Stack spacing={1.5}>
      {events.map((event) => (
        <Card key={event.id} variant="outlined">
          <CardActionArea
            component={RouterLink}
            to={`/projects/${projectId}/events/${event.id}`}
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
                <div>
                  <Typography variant="subtitle1" fontWeight={600}>
                    {event.event_no ? `${event.event_no} — ${event.title}` : event.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {event.event_date} at {event.event_time} &mdash;{" "}
                    {event.event_type}
                  </Typography>
                </div>
                <Stack direction="row" spacing={1}>
                  <Chip
                    label={event.severity}
                    color={severityColor(event.severity)}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={event.status}
                    color={statusColor(event.status)}
                    size="small"
                  />
                </Stack>
              </Stack>
            </CardContent>
          </CardActionArea>
        </Card>
      ))}
    </Stack>
  );
}

export default EventList;
