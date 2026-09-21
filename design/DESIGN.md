# Agreed interface direction

The supplied mockups are design references only. They are not embedded in the app or presented as a screenshot of the working build.

Image-first two-column workspace. Decorative personality belongs in header/footer edges, the empty state, and a compact loading card. The actual satellite image, answer and exported records remain clean.

Dark mode: deep navy, muted violet, teal. Day mode: soft light gray instead of pure white, navy text and readable secondary labels. Theme switching never alters satellite pixels. Theme selection persists locally. Honour reduced motion; never extend a real wait just to display an animation.

The user will generate original assets. Suggested pieces: one transparent logo; dark and light header-edge illustrations; dark and light compact loading illustrations; dark and light shallow footer landscapes. Reuse pieces where possible. Keep text out of artwork. Use transparent PNG/WebP where appropriate; consistent shapes, outlines and lighting. Text, counters and statuses remain real HTML.

The implemented CSS shapes reserve space while these assets are pending. No compass or metre scale is shown without validated geospatial metadata. No fictional progress percentage, confidence score or completed answer appears during inference.
