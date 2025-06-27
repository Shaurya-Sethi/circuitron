"""
Utility functions for the Circuitron system.
Contains formatting, printing, and other helper utilities.
"""

from typing import List
from agents.items import ReasoningItem
from .models import PlanOutput


def extract_reasoning_summary(run_result):
    """
    Return the concatenated model‐generated reasoning summary text
    from ResponseReasoningItem.raw_item.summary entries.
    """
    texts = []
    for item in run_result.new_items:
        if isinstance(item, ReasoningItem):
            # raw_item.summary is List[ResponseSummaryText]
            for chunk in item.raw_item.summary:
                if getattr(chunk, "type", None) == "summary_text":
                    texts.append(chunk.text)
    return "\n\n".join(texts).strip() or "(no summary returned)"


def print_section(title: str, items: List[str], bullet: str = "•", numbered: bool = False):
    """Helper function to print a section with consistent formatting."""
    if not items:
        return
    
    print(f"\n=== {title} ===")
    for i, item in enumerate(items):
        if numbered:
            print(f" {i+1}. {item}")
        else:
            print(f" {bullet} {item}")


def pretty_print_plan(plan: PlanOutput):
    """Pretty print a structured plan output."""
    # Section 0: Design Rationale (if provided)
    print_section("Design Rationale", plan.design_rationale)

    # Section 1: Schematic Overview
    print_section("Schematic Overview", plan.functional_blocks)

    # Section 2: Design Equations & Calculations
    if plan.design_equations:
        print_section("Design Equations & Calculations", plan.design_equations)
        
        # Show calculation results if available
        if plan.calculation_results:
            print("\n=== Calculated Values ===")
            for i, result in enumerate(plan.calculation_results):
                print(f" {i+1}. {result}")
    else:
        print("\n=== Design Equations & Calculations ===")
        print("No calculations required for this design.")

    # Section 3: Implementation Actions
    print_section("Implementation Steps", plan.implementation_actions, numbered=True)

    # Section 4: Component Search Queries
    print_section("Components to Search", plan.component_search_queries)

    # Section 5: SKiDL Notes
    print_section("Implementation Notes (SKiDL)", plan.implementation_notes)

    # Section 6: Limitations / Open Questions
    print_section("Design Limitations / Open Questions", plan.design_limitations)
    
    print()  # trailing newline


def crawl_documentation(base_url: str, doc_urls: List[str], output_file: str) -> bool:
    """
    Crawl documentation from a list of URLs and save as a single markdown file.
    
    This function uses crawl4ai to fetch content from multiple documentation pages
    and combines them into a comprehensive markdown document.
    
    Args:
        base_url: The base URL of the documentation site
        doc_urls: List of specific documentation URLs to crawl
        output_file: Path to the output markdown file
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        urls = [
            "https://example.com/docs/",
            "https://example.com/docs/quickstart/",
            "https://example.com/docs/api/"
        ]
        success = crawl_documentation(
            "https://example.com/docs/", 
            urls, 
            "example_docs.md"
        )
    """
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
        from datetime import datetime
        
        async def _crawl():
            browser_config = BrowserConfig(headless=True, verbose=False)
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=10,
                exclude_external_links=True,
                remove_overlay_elements=True,
                process_iframes=True
            )
            
            crawl_results = []
            async with AsyncWebCrawler(config=browser_config) as crawler:
                for url in doc_urls:
                    try:
                        result = await crawler.arun(url, config=run_config)
                        crawl_results.append(result)
                    except Exception as e:
                        print(f"Failed to crawl {url}: {e}")
                        
            # Save combined markdown
            if crawl_results:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                combined_content = [
                    f"# Documentation",
                    f"**Crawled from:** {base_url}",
                    f"**Generated on:** {current_time}",
                    f"**Total pages:** {len(crawl_results)}",
                    "", "---", ""
                ]
                
                for i, result in enumerate(crawl_results, 1):
                    if result.success:
                        combined_content.extend([
                            f"## Page {i}",
                            f"**Source URL:** {result.url}",
                            "---",
                            str(result.markdown),
                            "", "---", ""
                        ])
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(combined_content))
                return True
            return False
        
        return asyncio.run(_crawl())
        
    except ImportError:
        print("crawl4ai not installed. Install with: pip install crawl4ai")
        return False
    except Exception as e:
        print(f"Error crawling documentation: {e}")
        return False
