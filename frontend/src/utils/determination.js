// Display vocabulary for FIDIC Sub-Clause 3.7 determination states.
//
// Kept out of DeterminationPanel.jsx so that file exports components and
// nothing else - mixing constants in breaks Fast Refresh (and the
// react-refresh/only-export-components lint rule that guards it). Shared
// by the panel and the determination list so the two can't drift into
// describing the same state differently.

export const DETERMINATION_STATUS_LABELS = {
  UnderConsultation: "Engineer consulting (3.7.1)",
  Agreed: "Agreed — binding",
  AwaitingDetermination: "Awaiting determination (3.7.3)",
  DeterminedNodOpen: "Determined — NOD window open",
  NodGiven: "Notice of Dissatisfaction given",
  FinalAndBinding: "FINAL AND BINDING — no appeal",
  DeemedRejection: "Engineer's window lapsed — deemed rejection",
};

export const DETERMINATION_STATUS_COLORS = {
  UnderConsultation: "info",
  Agreed: "success",
  AwaitingDetermination: "warning",
  // Red on purpose: an open NOD window is a countdown to losing the
  // right to challenge the determination at all.
  DeterminedNodOpen: "error",
  NodGiven: "primary",
  FinalAndBinding: "default",
  DeemedRejection: "warning",
};
