# Fix: Slack "Invalid permissions requested" Error & Task Notifications

## Steps

### Backend Fix — Slack OAuth
- [x] Step 1: Analyze the code and identify the root cause
- [x] Step 2: Get user approval for the fix plan
- [x] Step 3: Update Slack OAuth scopes in `oauth_routes.py`:
  - Replace invalid `channels:write` with valid `channels:manage`
  - Add additional scopes for full bot functionality

### Backend Fix — Task Slack Notifications
- [x] Step 4: Add `slack_default_channel` setting to `settings.py` (default: `#all-janhvi`)
- [x] Step 5: Fix `router.py` — actually invoke `_post_slack_message_legacy` when tasks are created (both `create_task` and `confirm_plan` endpoints)
- [x] Step 6: The `_post_slack_message_legacy` function now reads `slack_default_channel` from settings and sends a formatted Slack message

### Configuration (User Action)
- [ ] Step 7: Add the same scopes in Slack App Dashboard → OAuth & Permissions → Bot Token Scopes (see list below)
- [ ] Step 8: Invite @SyncSphere bot to the #general channel in Slack
- [ ] Step 9: Restart the backend server (Docker/uvicorn) and test

