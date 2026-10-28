# Independent source review

A separate Sol agent reviewed the source and saved outputs without mutations or duplicated scientific execution.

Both guard-band-compliant fits are rejected by the fixed raw CT margin gate. This negative conclusion is supported; the results do not prove impossibility or measure anatomical registration error.

The first gradient trial is invalid for its declared support exclusion: derivative endpoints enter the guard band. Its failure and corrected rerun remain preserved.

The reserved exterior samples are withheld from the final optimizer call only. Both fits initialize from the earlier exterior corner-block fit, whose dense training blocks include some current reserved centers. For example, native (100,132,154) has reserved odd parity here but belongs to the earlier [96:104,128:136,152:160] training block. Its six gradient endpoints also lie in that earlier block. Furthermore, interleaved gradient stencils can share source voxels between training and reserve. Therefore reserved metrics are neither end-to-end unseen nor independent generalization evidence. The frozen plans' wording "never used by optimizer" must be interpreted with this correction; those originals remain unchanged.

Support exclusion is certified for old/native CT centers and central-difference endpoints only. No certificate is provided that all moving modern interpolation or quadrature supports avoid a corresponding swept exclusion band. This limitation does not change the negative gate result.

The repaired ROI was inspected before this follow-up. No claim of blind validation is justified. Later success would need an independently reserved spatial region and an initializer that has not used it, as well as the unchanged original gate; selecting a transform by the inspected ROI margin is not an acceptable substitute.
