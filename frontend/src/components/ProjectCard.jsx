import { Link as RouterLink } from "react-router-dom";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Chip from "@mui/material/Chip";
import { projectStatusColor } from "../theme";

function ProjectCard({ project }) {
  return (
    <Card variant="outlined">
      <CardActionArea component={RouterLink} to={`/projects/${project.id}`}>
        <CardContent>
          <Stack
            direction="row"
            sx={{ justifyContent: "space-between", alignItems: "flex-start", gap: 1 }}
          >
            <div>
              <Typography variant="subtitle1" fontWeight={600}>
                {project.project_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {project.project_code}
              </Typography>
            </div>
            <Chip
              label={project.status}
              color={projectStatusColor(project.status)}
              size="small"
            />
          </Stack>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {project.client_name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {project.city}, {project.country}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}

export default ProjectCard;
