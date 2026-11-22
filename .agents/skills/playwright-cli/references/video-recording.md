# Video Recording

Capture browser automation sessions as video for debugging, documentation, or verification. Produces WebM (VP8/VP9 codec).

## Basic Recording

```bash
# Open browser first
playwright-cli open

# Start recording, --cursor renders an animated mouse cursor that travels to each action point
# and paces actions by 800ms so that it has time to travel
playwright-cli video-start demo.webm --cursor --fps=60

# Add a chapter marker for section transitions
playwright-cli video-chapter "Getting Started" --description="Opening the homepage" --duration=2000

# Navigate and perform actions
playwright-cli goto https://example.com
playwright-cli snapshot
playwright-cli click e1

# Add another chapter
playwright-cli video-chapter "Filling Form" --description="Entering test data" --duration=2000
playwright-cli fill e2 "test input"

# Stop and save
playwright-cli video-stop
```

## Cursor, Target Highlight and Click Point

Three decorations can be drawn for each action: the mouse **cursor**, a **highlight** box around the
target element and a **point** marker at the click point. A **title** callout naming the action comes
with `video-show-actions`. The cursor is the only one `video-start --cursor` turns on; the rest are
opt-in and styled with plain CSS declarations, so they look exactly the way you want.

```bash
# Cursor only, nothing else on screen
playwright-cli video-start demo.webm --cursor

# Action callout, plus a red click point and a dark frame around the target
playwright-cli video-show-actions --duration=800 --position=top-right \
  --point-style="width: 20px; height: 20px; border-radius: 50%; background: rgba(255,0,0,.7)" \
  --highlight-style="outline: 2px solid #333; background: rgba(0,128,255,.15)" \
  --title-style="font-size: 16px"

# Stop annotating actions
playwright-cli video-hide-actions
```

The same options are available programmatically, which is the better choice for hero scripts:

```js
await page.screencast.showActions({
  // 'pointer' (default) animates the cursor from the previous action point, 'none' hides it.
  cursor: 'pointer',
  // How long decorations stay on screen. Actions are paced by this delay, 500ms by default.
  duration: 800,
  // Where the action title goes: top-left, top, top-right, bottom-left, bottom, bottom-right.
  position: 'top-right',
  style: {
    // Marker at the click point. The element is zero-sized and centered on the point,
    // so give it a size, or draw around the point with box-shadow. Hidden when omitted.
    point: 'width: 20px; height: 20px; border-radius: 50%; background: rgba(255, 0, 0, .7)',
    // Box that covers the target element. Hidden when omitted.
    // Prefer `outline` over `border`, it does not shrink the box.
    highlight: 'outline: 2px solid #333; background: rgba(0, 128, 255, .15)',
    // The action title. Use 'display: none' to keep the cursor but drop the callout.
    title: 'font-size: 16px',
  },
});
```

Notes:
- All decorations fade out over `duration`. Override `animation` in a style to do something else.
- The cursor stays on screen at the last action point between actions and across navigations,
  and travels along a slightly curved path, so it reads as a hand moving a mouse.
- Call `page.screencast.hideActions()` to stop annotating and hide the cursor.


## Devamı (ayrı dosyalar)
Bu dosya 150 satır sınırı için bölündü; içerik sırayla şu parçalarda sürer:
- [video-recording.part2.md](video-recording.part2.md): Best Practices · Tracing vs Video · Limitations
