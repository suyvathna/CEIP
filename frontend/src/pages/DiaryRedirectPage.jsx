import { useParams, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import { getDailyDiary } from "../api/dailyDiaries";
import { getEvent } from "../api/events";

/**
 * A diary now belongs to a project directly (see the daily diary
 * project-first change), with an optional event as a secondary link.
 * When there's a linked event, route through it (project id comes back
 * for free); when there isn't, the diary's own project_id is enough.
 */
function DiaryRedirectPage() {
  const { diaryId } = useParams();

  const diaryQuery = useQuery({
    queryKey: ["diary", diaryId],
    queryFn: () => getDailyDiary(diaryId),
  });

  const eventQuery = useQuery({
    queryKey: ["event", diaryQuery.data?.event_id],
    queryFn: () => getEvent(diaryQuery.data.event_id),
    enabled: Boolean(diaryQuery.data?.event_id),
  });

  if (diaryQuery.isLoading) {
    return <CircularProgress />;
  }

  if (diaryQuery.isError) {
    return <Alert severity="error">{diaryQuery.error.message}</Alert>;
  }

  if (!diaryQuery.data.event_id) {
    return (
      <Navigate to={`/projects/${diaryQuery.data.project_id}`} replace />
    );
  }

  if (eventQuery.isLoading) {
    return <CircularProgress />;
  }

  if (eventQuery.isError) {
    return <Alert severity="error">{eventQuery.error.message}</Alert>;
  }

  if (!eventQuery.data) {
    return <CircularProgress />;
  }

  return (
    <Navigate
      to={`/projects/${eventQuery.data.project_id}/events/${diaryQuery.data.event_id}`}
      replace
    />
  );
}

export default DiaryRedirectPage;
