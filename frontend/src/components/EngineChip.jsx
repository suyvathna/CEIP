import Chip from "@mui/material/Chip";
import Tooltip from "@mui/material/Tooltip";
import {
  ENGINE_COLORS,
  ENGINE_DESCRIPTIONS,
  ENGINE_LABELS,
  ENGINE_SHORT_LABELS,
} from "../utils/engines";

/**
 * Marks an item as Engine A or Engine B.
 *
 * Deliberately on every deadline, every alert and every screen header.
 * Before this existed there was no way to tell from the product which
 * loop had produced a given task, so "a thing with a date" was the only
 * available mental model - and that flattens the most important
 * distinction the platform makes, between a report you can send a day
 * late and a notice period that destroys an entitlement when it expires.
 */
function EngineChip({ engine, short = true, size = "small", ...props }) {
  if (!engine) return null;

  return (
    <Tooltip title={ENGINE_DESCRIPTIONS[engine] || ""}>
      <Chip
        size={size}
        variant="outlined"
        color={ENGINE_COLORS[engine] || "default"}
        label={
          short
            ? ENGINE_SHORT_LABELS[engine] || engine
            : ENGINE_LABELS[engine] || engine
        }
        {...props}
      />
    </Tooltip>
  );
}

export default EngineChip;
