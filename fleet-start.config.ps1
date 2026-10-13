# Per-repo fleet start config for demo-vid-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'demo-vid-mcp'
    BackendPort  = 11134
    FrontendPort = 11135
    HealthPath   = '/api/health'
    WebRoot      = 'webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'demo_vid_mcp.app:app'
        Env           = @{ WEB_PORT = '11134' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
