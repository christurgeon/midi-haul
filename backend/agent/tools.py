TOOLS = [
    {
        "name": "list_known_sources",
        "description": "Returns all scraper sources and their stats (file count, last scraped, error count).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "run_scraper",
        "description": "Runs a named scraper (bitmidi, vgmusic, freemidi, kunstderfuge) and returns how many new files were found and added.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Scraper name: bitmidi, vgmusic, freemidi, or kunstderfuge"},
                "max_files": {"type": "integer", "description": "Max MIDI files to process in this run", "default": 200},
            },
            "required": ["source"],
        },
    },
    {
        "name": "run_crawler",
        "description": "Runs the general web crawler on seed URLs to discover MIDI files from unlisted sites.",
        "input_schema": {
            "type": "object",
            "properties": {
                "seed_urls": {"type": "array", "items": {"type": "string"}, "description": "Starting URLs to crawl"},
                "max_depth": {"type": "integer", "description": "Max crawl depth", "default": 2},
                "max_files": {"type": "integer", "description": "Max MIDI files to process", "default": 100},
            },
            "required": ["seed_urls"],
        },
    },
    {
        "name": "search_web_for_midi_sources",
        "description": "Searches the web for pages that host MIDI files. Returns candidate URLs to crawl.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query, e.g. 'site with free MIDI files download'"}},
            "required": ["query"],
        },
    },
    {
        "name": "get_scrape_errors",
        "description": "Returns recent scraping errors. Use to decide whether to retry or skip a source.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Filter by source name (optional)"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name": "log_message",
        "description": "Appends a message to the agent run log visible in the UI. Use for progress updates.",
        "input_schema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    },
]
