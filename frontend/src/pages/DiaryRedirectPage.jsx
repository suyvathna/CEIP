import { useParams, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import { getDailyDiary } from "../api/dailyDiaries";
import { getEvent } from "../api/events";

/**
 * Same idea as EventRedirectPage, but a diary is two hops away from its
 * project: diary -> event -> project. Both are cheap, cached GETs.
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

  if (diaryQuery.isLoading || eventQuery.isLoading) {
    return <CircularProgress />;
  }

  if (diaryQuery.isError) {
    return <Alert severity="error">{diaryQuery.error.message}</Alert>;
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
