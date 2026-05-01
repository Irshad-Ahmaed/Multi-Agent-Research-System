from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from langchain_core.messages import HumanMessage, ToolMessage

def run_research_pipeline(topic: str) -> dict:
    state = {}

    # 1. search agent
    print("\n" + " ="*30)
    print("Step 1: Search Agent is working...")
    print("="*30)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({ 
        "messages": [
            HumanMessage(f"Find recent, reliable and detailed information about: {topic}")
        ]
    })

    tool_outputs = [m.content if isinstance(m.content, str) else str(m.content) for m in search_result['messages'] if isinstance(m, ToolMessage)]
    state['search_results'] = "\n\n".join(tool_outputs) or str(search_result['messages'][-1].content)

    print("\n Search Results:")
    print(state['search_results'])


    # 2. reader agent
    print("\n" + " ="*30)
    print("Step 2: Reader Agent is scraping the urls...")
    print("="*30)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [
            HumanMessage(
                f"You have search results about '{topic}'. "
                f"Your task is to:\n"
                f"1. Extract all URLs from the search results\n"
                f"2. Scrape each URL to get the full content\n"
                f"3. Return the scraped content with SOURCE URLS clearly labeled\n\n"
                f"Search Results:\n{state['search_results']}"
            )
        ]
    })
    state['reader_results'] = reader_result['messages'][-1].content

    print("\n Reader Results:")
    print(state['reader_results'])


    # 3. writer agent
    print("\n" + " ="*30)
    print("Step 3: Writer Agent is writing the research report...")
    print("="*30)

    combined_result = (
        f"SEARCH RESULTS: \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT: \n {state['reader_results']}"
    )

    state['report'] = writer_chain.invoke({
        "topic": topic,
        "research": combined_result
    })

    print("\n Research Report:")
    print(state['report'])

    # 4. critic agent
    print("\n" + " ="*30)
    print("Step 4: Critic Agent is evaluating the research report...")
    print("="*30)

    state['feedback'] = critic_chain.invoke({
        "report": state['report']
    })

    print("\n Feedback on the Research Report:")
    print(state['feedback'])

    return state


if __name__ == "__main__":
    topic = input("\n Enter a research topic: ")
    run_research_pipeline(topic)