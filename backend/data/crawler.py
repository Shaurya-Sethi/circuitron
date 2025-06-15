import asyncio
from crawl4ai import *

# This script uses the crawl4ai library to crawl the SKiDL documentation and GitHub repository.
skidl_sources = [
    "https://devbisme.github.io/skidl",                    # Main documentation (tutorials, guides)
]

async def main():
    async with AsyncWebCrawler() as crawler:
        for url in skidl_sources:
            # Each result will be a crawl of this URL and its internal links up to depth 2
            result = await crawler.arun(
                url=url,
                max_depth=2,       
                markdown=True,
                # max_pages=200,    # Optional safeguard—omit or increase if you want everything!
            )
            # Make a safe filename based on the URL
            fname = url.replace("https://", "").replace("/", "_").replace(":", "") + ".md"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(result.markdown)
            print(f"Crawled and saved: {fname}")

if __name__ == "__main__":
    asyncio.run(main())
