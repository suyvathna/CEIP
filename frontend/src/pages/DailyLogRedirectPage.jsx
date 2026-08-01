import { useParams, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import { getDailyLog } from "../api/dailyLogs";

/**
 * Search results only carry a Daily Log id, not its project id - this
 * resolves the id to its owning project and redirects to the real detail
 * page.
 */
function DailyLogRedirectPage() {
  const { dailyLogId } = useParams();

  const dailyLogQuery = useQuery({
    queryKey: ["dailyLog", dailyLogId],
    queryFn: () => getDailyLog(dailyLogId),
  });

  if (dailyLogQuery.isLoading) {
    return <CircularProgress />;
  }

  if (dailyLogQuery.isError) {
    return <Alert severity="error">{dailyLogQuery.error.message}</Alert>;
  }

  return (
    <Navigate
      to={`/projects/${dailyLogQuery.data.project_id}/daily-log/${dailyLogId}`}
      replace
    />
  );
}

export default DailyLogRedirectPage;
