# Progress Prize engineering submission draft

**Title**\
Exact CT plane reads and scalable candidate screening

**Contribution**\
We worked with native CT-derived inputs from PHerc0800, PHerc0175A, PHerc0813 and PHerc0191. We contribute two reusable improvements to scouting and rendering. The first plans exact byte ranges for required planes of compatible uncompressed CT chunks; the second avoids indexing points that are provably outside the axial distance gate used during candidate screening.

On PHerc0800 and PHerc0175A, the logged body bytes were 22.40% and 30.06% lower than reading the same complete uncompressed chunks. Three same-input PHerc0813 ranking replays were 7.55–14.20× faster in the ranking stage and preserved candidate geometry, threshold and order. The package provides reproducible standalone examples and recorded results. The changes address transfer volume and one ranking stage. The experiments do not claim equivalent savings for compressed sources or acceleration of the complete pipeline.

A complementary packed rival-mesh reconstruction in PHerc0191 used 56.5% and 64.4% less peak process memory in two matched runs, with byte-identical target and neighboring-surface mesh outputs. We include the hashes and the measured replay script.

**Evidence URL**\
Use the public project URL and the public release URL that includes the exact replay instructions and fixtures.
