import { useParams, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import { getEvent } from "../api/events";

/**
 * Intelligence search results only carry an event id, not the project it
 * belongs to (the project-scoped event routes need both). This route
 * resolves the event, then hands off to the real project-scoped URL.
 */
function EventRedirectPage() {
  const { eventId } = useParams();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["event", eventId],
    queryFn: () => getEvent(eventId),
  });

  if (isLoading) return <CircularProgress />;
  if (isError) return <Alert severity="error">{error.message}</Alert>;

  return (
    <Navigate to={`/projects/${data.project_id}/events/${eventId}`} replace />
  );
}

export default EventRedirectPage;
