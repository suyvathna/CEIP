import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Chip from "@mui/material/Chip";

function DiaryList({ diaries }) {
  if (diaries.length === 0) {
    return (
      <Typography color="text.secondary">
        No diary entries recorded yet.
      </Typography>
    );
  }

  return (
    <Stack spacing={1.5}>
      {diaries.map((diary) => (
        <Card key={diary.id} variant="outlined">
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
                {diary.diary_date}
              </Typography>
              {diary.linked_event_ids?.length > 0 && (
                <Chip
                  size="small"
                  variant="outlined"
                  label={`${diary.linked_event_ids.length} linked event${
                    diary.linked_event_ids.length === 1 ? "" : "s"
                  }`}
                />
              )}
            </Stack>
            {diary.work_completed && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                <strong>Work:</strong> {diary.work_completed}
              </Typography>
            )}
            {diary.manpower && (
              <Typography variant="body2" color="text.secondary">
                <strong>Manpower:</strong> {diary.manpower}
              </Typography>
            )}
            {diary.delays && (
              <Typography variant="body2" color="text.secondary">
                <strong>Delays:</strong> {diary.delays}
              </Typography>
            )}
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
}

export default DiaryList;
