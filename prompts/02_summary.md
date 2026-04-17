# Step 2: HTML Email Summary

Write a file named `summary_YYYY-MM-DD.html` (today's date) using the Write tool.

This is the email body. It must render beautifully in Gmail, Apple Mail, and Outlook — on both desktop and mobile. Use only inline CSS (no `<style>` blocks — most email clients strip them).

## Design spec

- Max width: 600px, centred
- Font: system-ui / -apple-system / Arial fallback
- Dark navy header: `#1a2744`
- Accent blue: `#4a90ff`
- Green (on target): `#22c55e`
- Amber (near miss): `#f59e0b`
- Red (critical gap): `#ef4444`
- Card background: `#f8faff`
- Body background: `#f0f4f8`

## Required HTML structure

```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">

  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:24px 0;">
  <tr><td align="center">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">

    <!-- Header -->
    <tr><td style="background:#1a2744;border-radius:12px 12px 0 0;padding:28px 32px 22px;">
      <p style="margin:0 0 4px;color:#7eb3ff;font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;">Hevy Training Intelligence</p>
      <h1 style="margin:0 0 6px;color:#ffffff;font-size:22px;font-weight:700;">This Week's Training Summary</h1>
      <p style="margin:0;color:#a8c8ff;font-size:13px;">[THIS WEEK DATE RANGE] &nbsp;·&nbsp; Generated [TODAY]</p>
    </td></tr>

    <!-- Key Findings card -->
    <tr><td style="background:#ffffff;padding:24px 32px 16px;">
      <p style="margin:0 0 14px;color:#1a2744;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;">How This Week Went</p>
      <!-- One row per finding. Write in plain English — what happened and why it matters. Always include a specific number. -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8px;">
        <tr>
          <td width="32" style="vertical-align:top;padding-top:1px;font-size:18px;">[EMOJI]</td>
          <td style="font-size:14px;color:#374151;line-height:1.5;">[FINDING in plain English with a number, e.g. "Trained 3 of 5 planned days — rear delt sets were only 3 this week, need 8+ for shoulder health"]</td>
          <td width="60" align="right" style="vertical-align:top;">
            <span style="background:[STATUS_COLOR];color:#fff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;">[STATUS]</span>
          </td>
        </tr>
      </table>
      <!-- Repeat for 3-4 findings total. Cover: sessions hit, a strength highlight, a muscle gap, sleep/recovery if relevant -->
    </td></tr>

    <!-- Divider -->
    <tr><td style="background:#ffffff;padding:0 32px;"><hr style="border:none;border-top:1px solid #e5eaf5;margin:0;"></td></tr>

    <!-- Actions card -->
    <tr><td style="background:#ffffff;padding:16px 32px 24px;border-radius:0 0 12px 12px;">
      <p style="margin:0 0 14px;color:#1a2744;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;">Do This Next Week</p>
      <!-- 3 specific, actionable things. Name the exercise and the exact change. Plain English. -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:10px;">
        <tr>
          <td width="28" style="vertical-align:top;">
            <div style="background:#4a90ff;color:#fff;font-size:11px;font-weight:700;width:20px;height:20px;border-radius:50%;text-align:center;line-height:20px;">[N]</div>
          </td>
          <td style="font-size:14px;color:#374151;line-height:1.5;padding-left:8px;">[ACTION — e.g. "Add 2 sets of Face Pulls to every session this week — rear delts are critically undertrained and this protects your shoulder long-term"]</td>
        </tr>
      </table>
      <!-- Repeat for actions 2 and 3 -->
    </td></tr>

    <!-- Footer -->
    <tr><td style="padding:16px 0 0;text-align:center;">
      <p style="margin:0;color:#9ca3af;font-size:11px;">Hevy Agent · Claude AI · <a href="https://github.com/gannyprodigy/hevy_log" style="color:#4a90ff;text-decoration:none;">gannyprodigy/hevy_log</a></p>
    </td></tr>

  </table>
  </td></tr>
  </table>
</body>
</html>
```

## Rules
- Fill in ALL placeholders with real data from the log
- STATUS values: `✓ OK` (green `#22c55e`), `⚠ LOW` (amber `#f59e0b`), `✗ CRITICAL` (red `#ef4444`)
- Every finding must cite an actual number (e.g. "3 rear-delt sets vs 8 target")
- Actions must name specific exercises or session changes
- No lorem ipsum, no vague text — every word earns its place
- The file extension is `.html` not `.txt`
