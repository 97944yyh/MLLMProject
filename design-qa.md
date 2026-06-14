source visual truth: user-provided RAGFlow knowledge-base screenshot in chat, plus requested DeepWiki-style translucent bottom input.
implementation target: http://127.0.0.1:7862
implementation screenshot: captured through the in-app browser for visual inspection; browser runtime could emit the image but could not save it to disk due filesystem permissions.
viewport: 1280 x 720
state: empty knowledge base before upload
full-view comparison evidence: visible browser render shows a light, two-pane knowledge-base workspace with chunk-list pane on the left, page preview pane on the right, compact upload controls, top stats, and a fixed translucent bottom query composer.
focused region comparison evidence: checked the bottom composer after revision; it is 61px tall at desktop viewport and contains only the prompt input plus query button, with mode and Top-K moved into the knowledge toolbar.

**Findings**
- No P0/P1/P2 issues remaining for the empty-state desktop layout.

**Patches Made**
- Reworked the old three-column teaching demo into a RAGFlow-style knowledge-base workspace.
- Renamed the database concept to knowledge-base viewing and removed the separate database panel idea.
- Removed the evidence file list from the main page.
- Changed the bottom query area from a tall control cluster to a translucent DeepWiki-like input composer.
- Moved retrieval mode and Top-K controls into the compact knowledge-base toolbar.
- Added CLI support for `--server-port` and `--server-name` so parallel local previews can run on different ports.

**Required Fidelity Surfaces**
- Fonts and typography: system sans stack, compact dashboard scale, no viewport-scaled type.
- Spacing and layout rhythm: two-pane workspace, 8px radii, compact toolbar, fixed bottom composer.
- Colors and visual tokens: light neutral surface, pale blue interaction accents, low-contrast borders, translucent panels.
- Image quality and asset fidelity: no custom fake document images are used before upload; actual rendered page previews are used after parsing.
- Copy and content: uses knowledge-base / evidence chunk terminology aligned to the revised brief.

final result: passed
