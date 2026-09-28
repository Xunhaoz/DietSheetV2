# DietSheet user guide

This guide describes the proposed self-hosted version; these features are not implemented yet.

## Daily use

1. Open the operator-provided HTTPS website and sign in. No Google Sheets connection setup is needed.
2. Add a meal with a 3:4 or 4:3 photo, meal type, capture time and optional portion notes. JPEG, PNG and WebP are supported; maximum 15 MiB and 24 megapixels.
3. A saved meal appears immediately. Image processing and nutrition analysis finish in the background. Failed analysis offers retry; avoid uploading the same meal again.
4. Select a date to review totals. Open the daily gallery to see the entire day on one scrolling page; open any card for the full image and analysis assumptions.
5. Use meal details to correct time, type or notes, or delete a record. Changing type/notes triggers new analysis. The previous estimate is marked stale while it is being replaced.

Missing values are shown as unknown. Partial totals identify unfinished estimates. A value of 125% means the recorded amount is 25% above the target; the graph shows that excess. Percentages describe recorded intake, not a nutrition score.

## Body measurements and goals

- **Body data:** enter a new dated measurement; correct or delete entries in history. The latest measurement appears in the sidebar. This does not automatically change food targets.
- **Nutrition goals:** set calories, carbohydrates, protein, fat and fiber with an effective date. Leave a target disabled when no comparison is wanted. Earlier days retain their earlier targets. Correcting or deleting a historical goal changes comparisons for its applicable dates.

The app supports a standard desktop layout, a compact Mac layout with the Dock visible, and a phone layout. Compact windows and phone screens scroll naturally; all editing actions remain available.

## Data and troubleshooting

Application data and images are stored on the owner's host. Gemini receives the low-resolution meal photo and its meal type/notes for analysis; it does not receive body history or nutrition goals. No Amazon service is used.

If analysis is delayed, the meal is still saved. If a refresh fails, keep the saved data visible and retry when the service returns. For an interrupted upload, retry the same submission. If a gallery page fails, retry loading that page. Ask the operator to reset a forgotten password or restore a backup.

Operators should follow the [deployment and recovery guide](../developer/delivery.md). Application access uses the configured HTTPS hostname; a public IP alone is not the complete access setup.
