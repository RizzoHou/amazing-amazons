Potential Improvements:
- Packed Move Structure: Change Move from a 6-byte struct (which aligns to 8 bytes) to a 4-byte uint32_t using bit-packing. This will reduce memory consumption for moves by 50%.
- BFS Depth Limit: The evaluation function relies on distances. Distances > 10 have negligible impact on the POW2 weights. you need to add a cutoff to the BFS to stop searching once the distance exceeds 10. This will significantly speed up leaf node evaluation.
- Precomputed Math: Add a precomputed log table for UCT calculations to avoid expensive std::log calls in the hot path.
- Fast Move Generation: Remove the Move class constructor overhead and inline move packing.