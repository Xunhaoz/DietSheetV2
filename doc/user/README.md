# DietSheet user guide

Guide to the proposed self-hosted version.

## Daily use

1. Open the operator-provided HTTPS website and sign in.
2. Add a meal with a 3:4 or 4:3 photo, meal type, capture time and optional portion notes. Only JPEG is supported. Resize the photo so its long edge is at most 1024 px (for example 1024x768 or 768x1024); larger photos are rejected. Maximum file size is 2 MiB.
3. A saved meal appears immediately. Image processing and nutrition analysis finish in the background. Use Retry to process a failed analysis again.
4. Select a date to review totals. Open the daily gallery to see the entire day on one scrolling page; open any card for the full image and analysis assumptions.
5. Use meal details to correct time, type or notes, or delete a record. Changing type/notes triggers new analysis. The previous estimate is marked stale while it is being replaced.

Missing values are shown as unknown. Partial totals identify unfinished estimates. A value of 125% means the recorded amount is 25% above the target; the graph shows that excess. Percentages compare recorded intake with the selected target.

## Body measurements and goals

- **Body data:** enter a new dated measurement; correct or delete entries in history. The latest measurement appears in the sidebar.
- **Nutrition goals:** set calories, carbohydrates, protein, fat and fiber with an effective date. Enable each target you want to track. Earlier days retain their earlier targets. Correcting or deleting a historical goal changes comparisons for its applicable dates.

The app supports a standard desktop layout, a compact Mac layout with the Dock visible, and a phone layout. Compact windows and phone screens scroll naturally; all editing actions remain available.

## Data and troubleshooting

Application data and images are stored on the owner's host. Gemini receives the low-resolution meal photo and its meal type/notes for analysis.

If analysis is delayed, the meal is still saved. If a refresh fails, keep the saved data visible and retry when the service returns. For an interrupted upload, retry the same submission. If a gallery page fails, retry loading that page. Ask the operator to reset a forgotten password or restore a backup.

Operators should follow the [deployment and recovery guide](../developer/delivery.md). Use the configured HTTPS hostname to access the application.
