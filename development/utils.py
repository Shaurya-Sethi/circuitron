"""
Utility functions for the Circuitron system.
Contains formatting, printing, and other helper utilities.
"""

from typing import List
from agents.items import ReasoningItem
from .models import PlanOutput, UserFeedback, PlanEditorOutput


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
                    "# Documentation",
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


def collect_user_feedback(plan: PlanOutput) -> UserFeedback:
    """
    Interactively collect user feedback on the design plan.
    This function prompts the user to answer open questions and request edits.
    """
    print("\n" + "="*60)
    print("PLAN REVIEW & FEEDBACK")
    print("="*60)
    
    feedback = UserFeedback()
    
    # Handle open questions if they exist
    if plan.design_limitations:
        print(f"\nThe planner has identified {len(plan.design_limitations)} open questions that need your input:")
        print("-" * 50)
        
        for i, question in enumerate(plan.design_limitations, 1):
            print(f"\n{i}. {question}")
            answer = input("   Your answer: ").strip()
            if answer:
                feedback.open_question_answers.append(f"Q{i}: {question}\nA: {answer}")
    
    # Collect general edits and modifications
    print("\n" + "-" * 50)
    print("OPTIONAL EDITS & MODIFICATIONS")
    print("-" * 50)
    print("Do you have any specific changes, clarifications, or modifications to request?")
    print("(Press Enter on empty line to finish)")
    
    edit_counter = 1
    while True:
        edit = input(f"Edit #{edit_counter}: ").strip()
        if not edit:
            break
        feedback.requested_edits.append(edit)
        edit_counter += 1
    
    # Collect additional requirements
    print("\n" + "-" * 50)
    print("ADDITIONAL REQUIREMENTS")
    print("-" * 50)
    print("Are there any new requirements or constraints not captured in the original design?")
    print("(Press Enter on empty line to finish)")
    
    req_counter = 1
    while True:
        req = input(f"Additional requirement #{req_counter}: ").strip()
        if not req:
            break
        feedback.additional_requirements.append(req)
        req_counter += 1
    
    return feedback


def format_plan_edit_input(original_prompt: str, plan: PlanOutput, feedback: UserFeedback) -> str:
    """
    Format the input for the PlanEdit Agent, combining all context.
    """
    input_parts = [
        "PLAN EDITING REQUEST",
        "=" * 50,
        "",
        "ORIGINAL USER PROMPT:",
        f'"""{original_prompt}"""',
        "",
        "GENERATED DESIGN PLAN:",
        "=" * 30,
    ]
    
    # Add each section of the plan
    if plan.design_rationale:
        input_parts.extend([
            "Design Rationale:",
            *[f"• {item}" for item in plan.design_rationale],
            ""
        ])
    
    if plan.functional_blocks:
        input_parts.extend([
            "Functional Blocks:",
            *[f"• {item}" for item in plan.functional_blocks],
            ""
        ])
    
    if plan.design_equations:
        input_parts.extend([
            "Design Equations:",
            *[f"• {item}" for item in plan.design_equations],
            ""
        ])
    
    if plan.calculation_results:
        input_parts.extend([
            "Calculation Results:",
            *[f"• {item}" for item in plan.calculation_results],
            ""
        ])
    
    if plan.implementation_actions:
        input_parts.extend([
            "Implementation Actions:",
            *[f"{i+1}. {item}" for i, item in enumerate(plan.implementation_actions)],
            ""
        ])
    
    if plan.component_search_queries:
        input_parts.extend([
            "Component Search Queries:",
            *[f"• {item}" for item in plan.component_search_queries],
            ""
        ])
    
    if plan.implementation_notes:
        input_parts.extend([
            "Implementation Notes:",
            *[f"• {item}" for item in plan.implementation_notes],
            ""
        ])
    
    if plan.design_limitations:
        input_parts.extend([
            "Design Limitations / Open Questions:",
            *[f"• {item}" for item in plan.design_limitations],
            ""
        ])
    
    # Add user feedback
    input_parts.extend([
        "USER FEEDBACK:",
        "=" * 30,
        ""
    ])
    
    if feedback.open_question_answers:
        input_parts.extend([
            "Answers to Open Questions:",
            *feedback.open_question_answers,
            ""
        ])
    
    if feedback.requested_edits:
        input_parts.extend([
            "Requested Edits:",
            *[f"• {edit}" for edit in feedback.requested_edits],
            ""
        ])
    
    if feedback.additional_requirements:
        input_parts.extend([
            "Additional Requirements:",
            *[f"• {req}" for req in feedback.additional_requirements],
            ""
        ])
    
    input_parts.extend([
        "INSTRUCTIONS:",
        "Analyze this feedback and determine whether to apply direct edits to the existing plan",
        "or trigger plan regeneration. Follow your decision framework carefully."
    ])
    
    return "\n".join(input_parts)


def pretty_print_edited_plan(edited_output: PlanEditorOutput):
    """Pretty print an edited plan output with change summary."""
    print("\n" + "="*60)
    print("PLAN SUCCESSFULLY UPDATED")
    print("="*60)
    
    print(f"\nAction: {edited_output.decision.action}")
    print(f"Reasoning: {edited_output.decision.reasoning}")
    
    if edited_output.changes_summary:
        print("\n" + "=" * 40)
        print("SUMMARY OF CHANGES")
        print("="*40)
        for i, change in enumerate(edited_output.changes_summary, 1):
            print(f"{i}. {change}")
    
    print("\n" + "=" * 40)
    print("UPDATED DESIGN PLAN")
    print("="*40)
    if edited_output.updated_plan:
        pretty_print_plan(edited_output.updated_plan)


def pretty_print_regeneration_prompt(regen_output: PlanEditorOutput):
    """Pretty print a regeneration prompt output."""
    print("\n" + "="*60)
    print("PLAN REGENERATION REQUIRED")
    print("=" * 60)
    
    print(f"\nAction: {regen_output.decision.action}")
    print(f"Reasoning: {regen_output.decision.reasoning}")
    
    if regen_output.regeneration_guidance:
        print("\n" + "=" * 40)
        print("REGENERATION GUIDANCE")
        print("="*40)
        for i, guidance in enumerate(regen_output.regeneration_guidance, 1):
            print(f"{i}. {guidance}")
    
    print("\n" + "=" * 40)
    print("RECONSTRUCTED PROMPT")
    print("="*40)
    print(regen_output.reconstructed_prompt)
