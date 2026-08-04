// The two logic loops, in the product's own words.
//
// These labels exist because the distinction is invisible from the item
// itself: "submit the monthly progress report" and "give a Notice of
// Claim" both read as a task with a date. The difference is WHY each one
// exists, and that is exactly what tells a PM how hard to run:
//
//   Engine A  the calendar requires it. It was going to be due whether
//             or not anything happened on site, and it comes round again
//             next month. Missing it is a breach.
//   Engine B  something happened and the contract started a clock. It is
//             one-off, it is usually a time-bar, and missing it destroys
//             a right rather than merely being a breach.
//
// Mirrors app/constants/notifications.py on the backend, which also
// serves them from GET /notifications/engines so the two can be checked
// against each other.

export const ENGINE_A = "A";
export const ENGINE_B = "B";

export const ENGINE_LABELS = {
  [ENGINE_A]: "Engine A · ALWAYS DO",
  [ENGINE_B]: "Engine B · DO-IN-CASE",
};

export const ENGINE_SHORT_LABELS = {
  [ENGINE_A]: "A · Always do",
  [ENGINE_B]: "B · Do-in-case",
};

export const ENGINE_DESCRIPTIONS = {
  [ENGINE_A]:
    "Routine, calendar-driven contract compliance — progress reports, Statements, programmes, close-out. Due whether or not anything goes wrong on site, and due again next month.",
  [ENGINE_B]:
    "Event-driven contractual clocks — claim time-bars (20.2), the Engineer's determination and your 28 days to object (3.7), and instructions that change the Works without being called Variations (3.5). Started by something that happened, and usually a time-bar.",
};

// Engine A is informational blue; Engine B is amber, because a clock is
// running. Not red - red is reserved for severity, and an Engine B item
// that is 60 days out is not an emergency.
export const ENGINE_COLORS = {
  [ENGINE_A]: "info",
  [ENGINE_B]: "warning",
};

// What each engine covers, for the explainer panels.
export const ENGINE_SCOPE = {
  [ENGINE_A]: [
    "Performance Security (4.2) and insurances (18.1)",
    "Initial and revised Programme (8.3)",
    "Monthly Progress Reports (4.20 / 4.21)",
    "Monthly Statement (14.3), the Engineer's IPC (14.6) and the Employer's payment (14.7)",
    "Statement at Completion (14.10), DNP (11.1) and Final Statement (14.11)",
  ],
  [ENGINE_B]: [
    "Event logged → Notice of Claim within 28 days (20.2.1)",
    "Notice → fully detailed claim within 84 days (20.2.4)",
    "Engineer to agree or determine (3.7.3)",
    "Notice of Dissatisfaction within 28 days of RECEIPT, or the determination is final and binding (3.7.5)",
    "Instruction not labelled a Variation → Notice before any work starts (3.5)",
  ],
};

export function engineForCategory(category) {
  return category === "Compliance" ? ENGINE_A : ENGINE_B;
}
