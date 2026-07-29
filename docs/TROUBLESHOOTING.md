# Troubleshooting

## Backend won't start
**Cause:** Port 11134 already in use  
**Fix:** Kill the process on that port, or change PORT in .env

## Voiceover fails
**Cause:** speech-mcp not running  
**Fix:** Start speech-mcp, or set SPEECH_MCP_URL in .env  
Check: `curl http://localhost:10909/health`

## Recording fails
**Cause:** Playwright browsers not installed  
**Fix:** `npx playwright install chromium` from webapp directory

## Composition fails
**Cause:** FFmpeg not installed  
**Fix:** `winget install FFmpeg`

## Empty Gallery
**Cause:** No videos generated yet  
**Fix:** Use `demo_vid_generate` tool to produce a video
