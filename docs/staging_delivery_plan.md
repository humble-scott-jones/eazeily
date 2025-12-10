# Staging Delivery Strategy (Dec 2025)

This document outlines the strategy to deliver all pending `staging/*` branches into a cohesive release.

## 1. Inventory of Staging Branches

The following branches are queued for delivery:

| Branch | Purpose | Priority/Order |
| --- | --- | --- |
| `staging/db-fix` | Fixes critical DB connection timeouts and compatibility. | **1. Foundation** |
| `staging/deps` | Updates dependencies (likely required by other features). | **2. Foundation** |
| `staging/tests` | Improvements to test suite/CI. | **3. Quality** |
| `staging/branding` | UI/Branding updates. | **4. Feature** |
| `staging/dashboard` | Dashboard features. | **4. Feature** |
| `staging/generator` | Core content generator updates. | **4. Feature** |
| `staging/publishing` | Publishing workflow features. | **4. Feature** |
| `staging/voice-profile` | Voice profile features. | **4. Feature** |
| `staging/rollout-2025-12-04` | Potential target integration branch? | **Target** |

## 2. Delivery Strategy

We will use a **Linear Integration** approach, merging branches one by one into a target integration branch. This isolates conflicts and allows for verification at each step.

### Phase 1: Foundation & Stability
1.  **[DEFERRED] `staging/db-fix`**: User requested to skip this due to complexity/delays. Will address DB rebuild/fix *after* features are merged.
2.  **Prepare Target Branch**: Use `staging/rollout-2025-12-04` as the base.
3.  **Merge `staging/deps`**: Ensure all dependencies are in place.
4.  **Merge `staging/tests`**: Ensure the test harness is robust.

### Phase 2: Feature Integration
Merge feature branches in order of complexity/risk (lowest to highest):
1.  `staging/branding` (Likely CSS/Templates, lower risk of logic conflict)
2.  `staging/dashboard`
3.  `staging/publishing`
4.  `staging/voice-profile`
5.  `staging/generator` (Core logic, highest risk of conflict)

### Phase 3: Verification & Release
1.  **Address DB Fix**: Revisit database connectivity/schema issues.
2.  Run full test suite (`./run_tests.sh`).
3.  Deploy to Staging environment.
3.  Manual verification of key flows (Login, Generate, Publish).
4.  Merge to `main` and Tag.

## 3. Immediate Next Steps

1.  **Resolve `staging/db-fix`**: We are currently mid-cherry-pick. We must finish this to have a clean "Foundation" block.
2.  **Verify `staging/rollout-2025-12-04`**: Check if this branch is suitable as the integration target.
3.  **Execute Merges**: Proceed with the merge order defined above.

## 4. Conflict Resolution Plan
- If a merge has complex conflicts, we will abort and assess if a **cherry-pick** strategy is better for that specific branch.
- We will use `git rerere` to remember resolutions if we need to re-do merges.
