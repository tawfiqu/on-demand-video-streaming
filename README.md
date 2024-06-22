# on-demand-video-streaming
On demand video streaming

## Current Design
- Upload endpoint uploads videos from the server to S3 using multi-part upload.
- Videos are processed locally for dash. In current implementation videos are served from the server.
